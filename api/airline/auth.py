from flask import Blueprint, current_app, g, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .access import create_token, login_required
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

    return jsonify(
        access_token=create_token(user),
        token_type="Bearer",
        expires_in=int(current_app.config["TOKEN_LIFETIME"].total_seconds()),
        user=public_user(user),
    )


@bp.post("/auth/logout")
@login_required()
def logout():
    # Invalidates every token issued to this user so far, not just the one used here
    db.users().update_one({"_id": g.user["_id"]}, {"$inc": {"token_version": 1}})
    return jsonify(message="Logged out.")


@bp.get("/me")
@login_required()
def profile():
    return jsonify(user=public_user(g.user))


@bp.delete("/me")
@login_required(role="user")
def delete_account():
    # Cancel the user's reservations first, so their tickets become available again
    for reservation in db.reservations().find({"user_email": g.user["email"]}):
        cancel_reservation(reservation)
    db.users().delete_one({"_id": g.user["_id"]})
    return "", 204
