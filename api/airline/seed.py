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


# (code, from, to, days ahead, (business seats, price), (economy seats, price))
SAMPLE_FLIGHTS = [
    ("ABC123", "New York", "London", 30, (50, 800), (100, 400)),
    ("DEF456", "Los Angeles", "Tokyo", 45, (20, 1200), (150, 600)),
    ("GHI789", "London", "Paris", 60, (30, 900), (80, 350)),
    ("ATH101", "Athens", "London", 5, (12, 520), (150, 140)),
    ("ATH102", "London", "Athens", 9, (12, 540), (150, 150)),
    ("ATH203", "Athens", "Paris", 7, (16, 480), (160, 120)),
    ("ATH204", "Paris", "Athens", 12, (16, 470), (160, 115)),
    ("ATH305", "Athens", "Rome", 4, (10, 320), (140, 85)),
    ("ATH306", "Rome", "Athens", 11, (10, 310), (140, 80)),
    ("ATH407", "Athens", "Berlin", 14, (14, 450), (170, 110)),
    ("ATH408", "Berlin", "Athens", 18, (14, 440), (170, 105)),
    ("ATH509", "Athens", "Larnaca", 3, (8, 260), (120, 75)),
    ("LCA510", "Larnaca", "Athens", 6, (8, 250), (120, 70)),
    ("ATH611", "Athens", "Thessaloniki", 2, (0, 180), (90, 45)),
    ("SKG612", "Thessaloniki", "Athens", 8, (6, 175), (0, 40)),
    ("ATH713", "Athens", "Heraklion", 10, (6, 160), (100, 38)),
    ("ATH714", "Athens", "Santorini", 20, (6, 210), (80, 65)),
    ("ATH815", "Athens", "Dubai", 25, (24, 1450), (220, 390)),
    ("ATH816", "Athens", "New York", 35, (30, 2900), (250, 620)),
    ("JFK917", "New York", "Athens", 40, (30, 2850), (250, 640)),
    ("LHR918", "London", "New York", 22, (40, 2400), (230, 480)),
    ("CDG919", "Paris", "Tokyo", 50, (28, 3100), (240, 780)),
    ("FRA920", "Frankfurt", "Singapore", 55, (32, 2800), (260, 690)),
    ("MAD921", "Madrid", "Lisbon", 16, (8, 230), (130, 60)),
    ("AMS922", "Amsterdam", "Barcelona", 28, (10, 290), (150, 85)),
    ("VIE923", "Vienna", "Athens", 33, (10, 360), (140, 95)),
    ("IST924", "Istanbul", "Athens", 38, (12, 300), (150, 90)),
    ("FCO925", "Rome", "Barcelona", 48, (10, 270), (140, 70)),
    ("SYD926", "Sydney", "Singapore", 70, (20, 2100), (200, 520)),
    ("DXB927", "Dubai", "Larnaca", 85, (16, 980), (180, 260)),
]


def sample_flight(code, departure, destination, days_ahead, business, economy):
    return {
        "code": code,
        "departure_airport": departure,
        "destination_airport": destination,
        # Relative to today, so sample flights are always in the future when inserted
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

    for flight in (sample_flight(*values) for values in SAMPLE_FLIGHTS):
        db.flights().update_one({"code": flight["code"]}, {"$setOnInsert": flight}, upsert=True)
        # Move departed sample flights forward again, so a long-running demo always has bookable flights
        db.flights().update_one(
            {"code": flight["code"], "flight_date": {"$lt": days_from_now(0)}},
            {"$set": {"flight_date": flight["flight_date"]}},
        )

    # Apply ADMIN_PASSWORD on every start, so changing it takes effect on an existing database
    if admin_password:
        db.users().update_one({"email": admin["email"]}, {"$set": {"password": admin["password"]}})
