from datetime import date, timedelta

from flask import current_app
from werkzeug.security import generate_password_hash

from . import db


def days_from_now(days):
    return (date.today() + timedelta(days=days)).isoformat()


def create_indexes():
    db.users().create_index("email", unique=True)
    db.flights().create_index("code", unique=True)
    db.flights().create_index("flight_date")
    db.reservations().create_index("reservation_code", unique=True)
    db.reservations().create_index("user_email")
    db.reservations().create_index("flight_code")


def sample_flight(code, departure, destination, days_ahead, business, economy):
    return {
        "code": code,
        "departure_airport": departure,
        "destination_airport": destination,
        # Relative to the first start, so the sample flights are always in the future
        "flight_date": days_from_now(days_ahead),
        "tickets": {
            "business": {"available": business[0], "price": business[1]},
            "economy": {"available": economy[0], "price": economy[1]},
        },
    }


def seed_database():
    """Insert the demo accounts and flights unless they already exist."""
    admin_password = current_app.config["ADMIN_PASSWORD"]
    admin = {
        "name": "John",
        "surname": "Doe",
        "email": "admin@example.com",
        "password": generate_password_hash(admin_password or "admin1234"),
        "date_of_birth": "2000-01-01",
        "country_of_origin": "Greece",
        "passport_number": "E20113",
        "role": "admin",
    }
    demo_user = {
        "name": "Nearchos",
        "surname": "Nikolaidis",
        "email": "nearchos@example.com",
        "password": generate_password_hash("user1234"),
        "date_of_birth": "2002-05-06",
        "country_of_origin": "Greece",
        "passport_number": "ABC123456",
        "role": "user",
    }
    for user in (admin, demo_user):
        db.users().update_one({"email": user["email"]}, {"$setOnInsert": user}, upsert=True)

    for flight in (
        sample_flight("ABC123", "New York", "London", 30, (50, 800), (100, 400)),
        sample_flight("DEF456", "Los Angeles", "Tokyo", 45, (20, 1200), (150, 600)),
        sample_flight("GHI789", "London", "Paris", 60, (30, 900), (80, 350)),
    ):
        db.flights().update_one({"code": flight["code"]}, {"$setOnInsert": flight}, upsert=True)

    # Apply ADMIN_PASSWORD on every start, so changing it takes effect on an existing database
    if admin_password:
        db.users().update_one({"email": admin["email"]}, {"$set": {"password": admin["password"]}})
