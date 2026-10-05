from flask import Blueprint, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .access import login_required
from .errors import APIError
from .reservations import cancel_reservation
from .validation import json_body, normalize_email, parse_past_date, require_text

bp = Blueprint("auth", __name__)

MIN_PASSWORD_LENGTH = 8


def public_user(user):
    fields = ("name", "surname", "email", "date_of_birth", "country_of_origin", "passport_number", "role")
    return {field: user.get(field) for field in fields}


@bp.post("/auth/register")
def register():
    data = json_body()
    user = require_text(data, "name", "surname", "email", "password", "date_of_birth", "country_of_origin", "passport_number")
    user["email"] = normalize_email(user["email"])
    user["date_of_birth"] = parse_past_date(user["date_of_birth"], "date_of_birth").isoformat()
    if len(user["password"]) < MIN_PASSWORD_LENGTH:
        raise APIError(400, f"password must be at least {MIN_PASSWORD_LENGTH} characters.")

    if db.users().find_one({"email": user["email"]}):
        raise APIError(409, "An account with this email already exists.")

    user["password"] = generate_password_hash(user["password"])
    user["role"] = "user"
    db.users().insert_one(user)
    return jsonify(message="Registration successful.", user=public_user(user)), 201


@bp.post("/auth/login")
def login():
    data = json_body()
    email = data.get("email").strip().lower() if isinstance(data.get("email"), str) else None
    password = data.get("password")

    user = db.users().find_one({"email": email}) if email else None
    if not user or not isinstance(password, str) or not check_password_hash(user["password"], password):
        raise APIError(401, "Wrong email or password.")

    session.clear()
    session["email"] = user["email"]
    session["role"] = user["role"]
    session.permanent = True
    return jsonify(message="Logged in.", user=public_user(user))


@bp.post("/auth/logout")
@login_required()
def logout():
    session.clear()
    return jsonify(message="Logged out.")


@bp.get("/me")
@login_required()
def profile():
    user = db.users().find_one({"email": session["email"]})
    if not user:
        session.clear()
        raise APIError(401, "Your account no longer exists.")
    return jsonify(user=public_user(user))


@bp.delete("/me")
@login_required(role="user")
def delete_account():
    # Cancel the user's reservations first, so their tickets become available again
    for reservation in db.reservations().find({"user_email": session["email"]}):
        cancel_reservation(reservation)
    db.users().delete_one({"email": session["email"]})
    session.clear()
    return "", 204
