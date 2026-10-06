import os
import uuid
from datetime import date, timedelta

import pytest
from pymongo import MongoClient

from airline import create_app

MONGO_URI = os.environ.get("TEST_MONGO_URI", "mongodb://localhost:27017")


def days_from_now(days):
    return (date.today() + timedelta(days=days)).isoformat()


@pytest.fixture
def app():
    # Each test gets its own throwaway database
    db_name = f"airline_test_{uuid.uuid4().hex[:12]}"
    app = create_app(
        {
            "TESTING": True,
            "MONGO_URI": MONGO_URI,
            "MONGO_DB": db_name,
            "SECRET_KEY": "test-secret-key-that-is-at-least-32-bytes",
            "ADMIN_PASSWORD": None,
        }
    )
    yield app
    MongoClient(MONGO_URI).drop_database(db_name)


@pytest.fixture
def anon(app):
    return app.test_client()


def logged_in(app, email, password):
    """A test client that sends the user's access token with every request."""
    client = app.test_client()
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    client.environ_base["HTTP_AUTHORIZATION"] = "Bearer " + response.get_json()["access_token"]
    return client


@pytest.fixture
def admin(app):
    return logged_in(app, "admin@example.com", "admin1234")


@pytest.fixture
def user(app):
    return logged_in(app, "nearchos@example.com", "user1234")


@pytest.fixture
def new_flight():
    def build(**overrides):
        flight = {
            "departure_airport": "Athens",
            "destination_airport": "Rome",
            "flight_date": days_from_now(10),
            "tickets": {"business": {"available": 2, "price": 300}, "economy": {"available": 1, "price": 120.5}},
        }
        flight.update(overrides)
        return flight

    return build


@pytest.fixture
def passenger():
    return {
        "first_name": "Maria",
        "last_name": "Papadopoulou",
        "passport_number": "AE123456",
        "date_of_birth": "1990-04-12",
        "email": "maria@example.com",
    }
