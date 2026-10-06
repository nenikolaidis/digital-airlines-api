from datetime import date, datetime, timezone

from flask import Blueprint, g, jsonify, url_for

from . import db
from .access import login_required
from .errors import APIError
from .flights import get_flight_or_404
from .pagination import paginate
from .validation import json_body, normalize_email, parse_past_date, parse_ticket_class, require_text

bp = Blueprint("reservations", __name__, url_prefix="/reservations")


def reservation_view(reservation, flight=None):
    view = {
        "reservation_code": reservation["reservation_code"],
        "flight_code": reservation["flight_code"],
        "ticket_class": reservation["ticket_class"],
        "price": reservation["price"],
        "booked_at": reservation["booked_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "passenger": reservation["passenger"],
    }
    if flight:
        view["flight"] = {
            "departure_airport": flight["departure_airport"],
            "destination_airport": flight["destination_airport"],
            "flight_date": flight["flight_date"],
        }
    return view


def get_own_reservation_or_404(code):
    reservation = db.reservations().find_one({"reservation_code": code.upper(), "user_email": g.user["email"]})
    if not reservation:
        raise APIError(404, f"Reservation {code} not found.")
    return reservation


def cancel_reservation(reservation):
    # Delete first and only then release the ticket, so a double cancel can't release it twice
    if db.reservations().delete_one({"_id": reservation["_id"]}).deleted_count:
        db.flights().update_one(
            {"code": reservation["flight_code"]},
            {"$inc": {"tickets.{}.available".format(reservation["ticket_class"]): 1}},
        )


@bp.post("")
@login_required(role="user")
def create_reservation():
    data = json_body()
    fields = require_text(data, "flight_code", "ticket_class")
    ticket_class = parse_ticket_class(fields["ticket_class"])

    if not isinstance(data.get("passenger"), dict):
        raise APIError(400, "passenger must be an object with first_name, last_name, passport_number, date_of_birth and email.")
    passenger = require_text(data["passenger"], "first_name", "last_name", "passport_number", "date_of_birth", "email")
    passenger["email"] = normalize_email(passenger["email"], "passenger.email")
    passenger["date_of_birth"] = parse_past_date(passenger["date_of_birth"], "passenger.date_of_birth").isoformat()

    flight = get_flight_or_404(fields["flight_code"])
    today = date.today().isoformat()
    if flight["flight_date"] < today:
        raise APIError(409, "Flight {} has already departed.".format(flight["code"]))

    # Take a ticket only if one is left, in a single atomic update
    available = f"tickets.{ticket_class}.available"
    flight = db.flights().find_one_and_update(
        {"_id": flight["_id"], available: {"$gt": 0}, "flight_date": {"$gte": today}},
        {"$inc": {available: -1}},
    )
    if not flight:
        raise APIError(409, f"No {ticket_class} tickets are left on this flight.")

    reservation = {
        "flight_code": flight["code"],
        "user_email": g.user["email"],
        "ticket_class": ticket_class,
        "price": flight["tickets"][ticket_class]["price"],
        "booked_at": datetime.now(timezone.utc),
        "passenger": passenger,
    }
    try:
        code = db.insert_with_code(db.reservations(), reservation, "reservation_code")
    except Exception:
        db.flights().update_one({"_id": flight["_id"]}, {"$inc": {available: 1}})
        raise

    location = url_for(".get_reservation", code=code)
    return jsonify(reservation=reservation_view(reservation, flight)), 201, {"Location": location}


@bp.get("")
@login_required(role="user")
def list_reservations():
    query = {"user_email": g.user["email"]}
    meta, reservations = paginate(db.reservations(), query, [("booked_at", 1), ("_id", 1)], reservation_view)
    return jsonify(**meta, reservations=reservations)


@bp.get("/<code>")
@login_required(role="user")
def get_reservation(code):
    reservation = get_own_reservation_or_404(code)
    flight = db.flights().find_one({"code": reservation["flight_code"]})
    return jsonify(reservation=reservation_view(reservation, flight))


@bp.delete("/<code>")
@login_required(role="user")
def delete_reservation(code):
    reservation = get_own_reservation_or_404(code)
    flight = db.flights().find_one({"code": reservation["flight_code"]})
    if flight and flight["flight_date"] < date.today().isoformat():
        raise APIError(409, "Reservations for departed flights can't be cancelled.")
    cancel_reservation(reservation)
    return "", 204
