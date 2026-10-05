from airline import db


def book(client, passenger, flight_code="ABC123", ticket_class="economy"):
    return client.post("/reservations", json={"flight_code": flight_code, "ticket_class": ticket_class, "passenger": passenger})


def available(anon, flight_code, ticket_class):
    return anon.get(f"/flights/{flight_code}").get_json()["flight"]["tickets"][ticket_class]["available"]


def test_book_and_view_reservation(user, anon, passenger):
    response = book(user, passenger, ticket_class="business")
    assert response.status_code == 201
    reservation = response.get_json()["reservation"]
    assert reservation["price"] == 800
    assert reservation["flight"]["destination_airport"] == "London"
    assert available(anon, "ABC123", "business") == 49

    code = reservation["reservation_code"]
    assert user.get(f"/reservations/{code}").get_json()["reservation"]["passenger"]["last_name"] == "Papadopoulou"
    listing = user.get("/reservations").get_json()
    assert listing["count"] == 1
    assert listing["reservations"][0]["reservation_code"] == code


def test_empty_reservation_list_is_not_an_error(user):
    response = user.get("/reservations")
    assert response.status_code == 200
    assert response.get_json() == {"count": 0, "reservations": []}


def test_cancel_releases_ticket(user, anon, passenger):
    code = book(user, passenger).get_json()["reservation"]["reservation_code"]
    assert available(anon, "ABC123", "economy") == 99

    assert user.delete(f"/reservations/{code}").status_code == 204
    assert available(anon, "ABC123", "economy") == 100
    assert user.delete(f"/reservations/{code}").status_code == 404
    assert available(anon, "ABC123", "economy") == 100


def test_sold_out_class_is_refused(admin, user, passenger, new_flight):
    code = admin.post("/flights", json=new_flight()).get_json()["flight"]["code"]
    assert book(user, passenger, code).status_code == 201
    response = book(user, passenger, code)
    assert response.status_code == 409
    assert "No economy tickets" in response.get_json()["error"]


def test_departed_flight_cannot_be_booked(app, user, passenger):
    with app.app_context():
        db.flights().update_one({"code": "ABC123"}, {"$set": {"flight_date": "2020-01-01"}})
    assert book(user, passenger).status_code == 409


def test_booking_validation(user, passenger):
    assert book(user, passenger, ticket_class="first").status_code == 400
    assert book(user, passenger, flight_code="NOPE00").status_code == 404
    assert book(user, {**passenger, "email": "nope"}).status_code == 400
    assert book(user, {**passenger, "date_of_birth": "2999-01-01"}).status_code == 400
    assert book(user, {k: v for k, v in passenger.items() if k != "passport_number"}).status_code == 400
    assert user.post("/reservations", json={"flight_code": "ABC123", "ticket_class": "economy"}).status_code == 400


def test_users_only_see_their_own_reservations(app, user, anon, passenger):
    code = book(user, passenger).get_json()["reservation"]["reservation_code"]

    anon.post(
        "/auth/register",
        json={
            "name": "Other",
            "surname": "Person",
            "email": "other@example.com",
            "password": "other-pass",
            "date_of_birth": "1990-01-01",
            "country_of_origin": "Greece",
            "passport_number": "X1",
        },
    )
    anon.post("/auth/login", json={"email": "other@example.com", "password": "other-pass"})
    assert anon.get(f"/reservations/{code}").status_code == 404
    assert anon.delete(f"/reservations/{code}").status_code == 404
    assert anon.get("/reservations").get_json()["count"] == 0
    assert user.get(f"/reservations/{code}").status_code == 200


def test_reservations_need_a_user_session(anon, admin, passenger):
    assert anon.get("/reservations").status_code == 401
    assert book(admin, passenger).status_code == 403
