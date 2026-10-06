from datetime import date

from flask import Blueprint, jsonify, request, url_for
from pymongo.collation import Collation

from . import db
from .access import login_required, optional_user
from .errors import APIError
from .validation import TICKET_CLASSES, json_body, parse_date, parse_number, require_text

bp = Blueprint("flights", __name__, url_prefix="/flights")

# Compare airport names ignoring case ("london" matches "London")
CASE_INSENSITIVE = Collation(locale="en", strength=2)


def flight_summary(flight):
    return {
        "code": flight["code"],
        "departure_airport": flight["departure_airport"],
        "destination_airport": flight["destination_airport"],
        "flight_date": flight["flight_date"],
        "tickets": flight["tickets"],
    }


def get_flight_or_404(code):
    flight = db.flights().find_one({"code": code.upper()})
    if not flight:
        raise APIError(404, f"Flight {code} not found.")
    return flight


def parse_tickets(tickets):
    # Expects {"business": {"available": 50, "price": 800}, "economy": {...}}
    if not isinstance(tickets, dict) or set(tickets) != set(TICKET_CLASSES):
        raise APIError(400, "tickets must contain exactly these classes: {}.".format(", ".join(TICKET_CLASSES)))
    parsed = {}
    for ticket_class, values in tickets.items():
        if not isinstance(values, dict):
            raise APIError(400, f"tickets.{ticket_class} must be an object with available and price.")
        parsed[ticket_class] = {
            "available": parse_number(values.get("available"), f"tickets.{ticket_class}.available", integer=True),
            "price": parse_number(values.get("price"), f"tickets.{ticket_class}.price"),
        }
    return parsed


@bp.get("")
def list_flights():
    query = {}
    for param, field in (("from", "departure_airport"), ("to", "destination_airport")):
        value = request.args.get(param, "").strip()
        if value:
            query[field] = value

    if request.args.get("date"):
        query["flight_date"] = parse_date(request.args["date"], "date").isoformat()
    else:
        date_range = {}
        if request.args.get("date_from"):
            date_range["$gte"] = parse_date(request.args["date_from"], "date_from").isoformat()
        if request.args.get("date_to"):
            date_range["$lte"] = parse_date(request.args["date_to"], "date_to").isoformat()
        if date_range:
            query["flight_date"] = date_range

    # Dates are stored as YYYY-MM-DD strings, so sorting them as text sorts them by date
    flights = db.flights().find(query, collation=CASE_INSENSITIVE).sort([("flight_date", 1), ("code", 1)])
    results = [flight_summary(flight) for flight in flights]
    return jsonify(count=len(results), flights=results)


@bp.get("/<code>")
def get_flight(code):
    flight = get_flight_or_404(code)
    response = flight_summary(flight)

    # Only admins see who is booked on the flight
    user = optional_user()
    if user and user["role"] == "admin":
        response["reservations"] = [
            {
                "reservation_code": reservation["reservation_code"],
                "passenger_name": "{} {}".format(reservation["passenger"]["first_name"], reservation["passenger"]["last_name"]),
                "ticket_class": reservation["ticket_class"],
            }
            for reservation in db.reservations().find({"flight_code": flight["code"]})
        ]
    return jsonify(flight=response)


@bp.post("")
@login_required(role="admin")
def create_flight():
    data = json_body()
    fields = require_text(data, "departure_airport", "destination_airport", "flight_date")
    if fields["departure_airport"].casefold() == fields["destination_airport"].casefold():
        raise APIError(400, "departure_airport and destination_airport must be different.")

    flight_date = parse_date(fields["flight_date"], "flight_date")
    if flight_date < date.today():
        raise APIError(400, "flight_date can't be in the past.")

    flight = {
        "departure_airport": fields["departure_airport"],
        "destination_airport": fields["destination_airport"],
        "flight_date": flight_date.isoformat(),
        "tickets": parse_tickets(data.get("tickets")),
    }
    code = db.insert_with_code(db.flights(), flight, "code")
    return jsonify(flight=flight_summary(flight)), 201, {"Location": url_for(".get_flight", code=code)}


@bp.patch("/<code>")
@login_required(role="admin")
def update_prices(code):
    # Only prices can change: availability is managed by bookings
    tickets = json_body().get("tickets")
    if not isinstance(tickets, dict) or not tickets:
        raise APIError(400, 'Send new prices as {"tickets": {"economy": {"price": 420}}}.')

    updates = {}
    for ticket_class, values in tickets.items():
        if ticket_class not in TICKET_CLASSES:
            raise APIError(400, f"Unknown ticket class: {ticket_class}.")
        if not isinstance(values, dict) or set(values) != {"price"}:
            raise APIError(400, f"Only the price of tickets.{ticket_class} can be changed.")
        updates[f"tickets.{ticket_class}.price"] = parse_number(values["price"], f"tickets.{ticket_class}.price")

    flight = get_flight_or_404(code)
    db.flights().update_one({"_id": flight["_id"]}, {"$set": updates})
    return jsonify(flight=flight_summary(get_flight_or_404(code)))


@bp.delete("/<code>")
@login_required(role="admin")
def delete_flight(code):
    flight = get_flight_or_404(code)
    if db.reservations().find_one({"flight_code": flight["code"]}):
        raise APIError(409, "Flight {} has reservations and can't be deleted.".format(flight["code"]))
    db.flights().delete_one({"_id": flight["_id"]})
    return "", 204
