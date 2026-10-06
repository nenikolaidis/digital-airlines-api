from conftest import days_from_now, sample_codes


def test_search_is_public_and_sorted_by_date(anon):
    response = anon.get("/flights?per_page=100")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == len(sample_codes())
    assert [flight["code"] for flight in data["flights"]] == sample_codes()
    assert all(flight["flight_date"] > days_from_now(0) for flight in data["flights"])


def test_search_filters_are_case_insensitive(anon):
    flights = anon.get("/flights?from=new york&to=LONDON").get_json()["flights"]
    assert [flight["code"] for flight in flights] == sample_codes(lambda f: f[:2] == ("New York", "London"))


def test_search_by_date_and_range(anon):
    on_day_45 = anon.get(f"/flights?date={days_from_now(45)}").get_json()["flights"]
    assert [f["code"] for f in on_day_45] == sample_codes(lambda f: f[2] == 45)
    in_range = anon.get(f"/flights?date_from={days_from_now(40)}&date_to={days_from_now(70)}&per_page=100").get_json()
    assert [f["code"] for f in in_range["flights"]] == sample_codes(lambda f: 40 <= f[2] <= 70)
    response = anon.get("/flights?date=05-07-2026")
    assert response.status_code == 400
    assert "YYYY-MM-DD" in response.get_json()["error"]


def test_flight_details_hide_passengers_from_non_admins(anon, user, admin, passenger):
    user.post("/reservations", json={"flight_code": "GHI789", "ticket_class": "business", "passenger": passenger})

    assert "reservations" not in anon.get("/flights/GHI789").get_json()["flight"]
    assert "reservations" not in user.get("/flights/ghi789").get_json()["flight"]
    reservations = admin.get("/flights/GHI789").get_json()["flight"]["reservations"]
    assert [r["passenger_name"] for r in reservations] == ["Maria Papadopoulou"]


def test_unknown_flight_is_404(anon):
    assert anon.get("/flights/NOPE00").status_code == 404


def test_admin_creates_flight(admin, anon, new_flight):
    response = admin.post("/flights", json=new_flight())
    assert response.status_code == 201
    flight = response.get_json()["flight"]
    assert len(flight["code"]) == 6
    assert response.headers["Location"].endswith("/flights/{}".format(flight["code"]))
    assert anon.get("/flights/{}".format(flight["code"])).get_json()["flight"]["tickets"]["economy"]["price"] == 120.5


def test_only_admins_create_flights(anon, user, new_flight):
    assert anon.post("/flights", json=new_flight()).status_code == 401
    assert user.post("/flights", json=new_flight()).status_code == 403


def test_create_flight_validation(admin, new_flight):
    bad_tickets = {"business": {"available": 2, "price": 300}, "economy": {"available": -1, "price": 10}}
    cases = [
        new_flight(flight_date=days_from_now(-1)),
        new_flight(flight_date="2026/12/01"),
        new_flight(destination_airport="athens"),
        new_flight(departure_airport=""),
        new_flight(tickets=bad_tickets),
        new_flight(tickets={"economy": {"available": 1, "price": 10}}),
        new_flight(tickets={"business": {"available": 1.5, "price": 1}, "economy": {"available": 1, "price": 1}}),
        new_flight(tickets={"business": {"available": 1, "price": "nan"}, "economy": {"available": 1, "price": 1}}),
        new_flight(tickets={"business": {"available": True, "price": 1}, "economy": {"available": 1, "price": 1}}),
    ]
    for payload in cases:
        assert admin.post("/flights", json=payload).status_code == 400, payload


def test_update_prices(admin):
    response = admin.patch("/flights/ABC123", json={"tickets": {"economy": {"price": 420}}})
    assert response.status_code == 200
    tickets = response.get_json()["flight"]["tickets"]
    assert tickets["economy"]["price"] == 420
    assert tickets["business"]["price"] == 800

    # Sending the same price again is not an error
    assert admin.patch("/flights/ABC123", json={"tickets": {"economy": {"price": 420}}}).status_code == 200


def test_update_prices_validation(admin):
    assert admin.patch("/flights/ABC123", json={"tickets": {"economy": {"price": -5}}}).status_code == 400
    assert admin.patch("/flights/ABC123", json={"tickets": {"economy": {"available": 999}}}).status_code == 400
    assert admin.patch("/flights/ABC123", json={"tickets": {"first": {"price": 5}}}).status_code == 400
    assert admin.patch("/flights/ABC123", json={}).status_code == 400
    assert admin.patch("/flights/NOPE00", json={"tickets": {"economy": {"price": 5}}}).status_code == 404


def test_delete_flight(admin, anon, user, passenger):
    response = user.post("/reservations", json={"flight_code": "DEF456", "ticket_class": "economy", "passenger": passenger})
    assert admin.delete("/flights/DEF456").status_code == 409

    user.delete("/reservations/{}".format(response.get_json()["reservation"]["reservation_code"]))
    assert admin.delete("/flights/DEF456").status_code == 204
    assert anon.get("/flights/DEF456").status_code == 404


def test_restart_moves_departed_sample_flights_forward(app, anon, restart):
    from airline import db

    with app.app_context():
        db.flights().update_one({"code": "ABC123"}, {"$set": {"flight_date": "2020-01-01"}})
    restart()

    assert anon.get("/flights/ABC123").get_json()["flight"]["flight_date"] == days_from_now(30)
    # Sample flights that haven't departed keep their date
    assert anon.get("/flights/GHI789").get_json()["flight"]["flight_date"] == days_from_now(60)


def test_search_is_paginated(anon):
    total = len(sample_codes())
    first = anon.get("/flights?per_page=12").get_json()
    assert {k: first[k] for k in ("page", "per_page", "total", "pages", "count")} == {
        "page": 1,
        "per_page": 12,
        "total": total,
        "pages": -(-total // 12),
        "count": 12,
    }
    pages = [anon.get(f"/flights?per_page=12&page={page}").get_json() for page in range(1, first["pages"] + 1)]
    assert [f["code"] for page in pages for f in page["flights"]] == sample_codes()
    assert pages[-1]["count"] == total - 12 * (first["pages"] - 1)

    # Past the last page there are no results, but it isn't an error
    assert anon.get(f"/flights?per_page=12&page={first['pages'] + 1}").get_json()["flights"] == []


def test_pagination_counts_only_matching_flights(anon):
    from_london = len(sample_codes(lambda f: f[0] == "London"))
    data = anon.get("/flights?from=london&per_page=1").get_json()
    assert (data["total"], data["pages"]) == (from_london, from_london)


def test_pagination_validation(anon):
    for query in ("page=0", "page=-1", "page=abc", "per_page=0", "per_page=101", "per_page=2.5"):
        response = anon.get(f"/flights?{query}")
        assert response.status_code == 400, query
        assert query.split("=")[0] in response.get_json()["error"]
