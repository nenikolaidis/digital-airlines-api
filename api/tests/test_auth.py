from datetime import timedelta

from conftest import logged_in


def register_payload(**overrides):
    payload = {
        "name": "Eleni",
        "surname": "Georgiou",
        "email": "eleni@example.com",
        "password": "s3cure-pass",
        "date_of_birth": "1998-02-01",
        "country_of_origin": "Cyprus",
        "passport_number": "K998877",
    }
    payload.update(overrides)
    return payload


def test_index_lists_endpoints(anon):
    response = anon.get("/")
    assert response.status_code == 200
    assert "POST /reservations" in response.get_json()["endpoints"]
    assert "GET /flights/{code}" in response.get_json()["endpoints"]


def test_register_then_login_with_any_email_case(app, anon):
    response = anon.post("/auth/register", json=register_payload(email="  Eleni@Example.COM "))
    assert response.status_code == 201
    user = response.get_json()["user"]
    assert user["email"] == "eleni@example.com"
    assert user["role"] == "user"
    assert "password" not in user

    client = logged_in(app, "ELENI@example.com", "s3cure-pass")
    assert client.get("/me").get_json()["user"]["email"] == "eleni@example.com"


def test_register_rejects_duplicate_email(anon):
    anon.post("/auth/register", json=register_payload())
    response = anon.post("/auth/register", json=register_payload(email="ELENI@example.com"))
    assert response.status_code == 409


def test_register_validation(anon):
    cases = [
        (register_payload(name=""), "name"),
        (register_payload(email="not-an-email"), "email"),
        (register_payload(password="short"), "password"),
        (register_payload(date_of_birth="01-02-1998"), "date_of_birth"),
        (register_payload(date_of_birth="2999-01-01"), "date_of_birth"),
    ]
    for payload, field in cases:
        response = anon.post("/auth/register", json=payload)
        assert response.status_code == 400, payload
        assert field in response.get_json()["error"]


def test_non_json_body_is_rejected(anon):
    response = anon.post("/auth/register", data={"name": "x"})
    assert response.status_code == 400
    assert "JSON" in response.get_json()["error"]


def test_wrong_password_is_401(anon):
    response = anon.post("/auth/login", json={"email": "admin@example.com", "password": "nope"})
    assert response.status_code == 401
    assert response.get_json() == {"error": "Wrong email or password."}


def test_unknown_email_is_401(anon):
    response = anon.post("/auth/login", json={"email": "ghost@example.com", "password": "whatever"})
    assert response.status_code == 401


def test_login_returns_a_bearer_token(anon):
    data = anon.post("/auth/login", json={"email": "nearchos@example.com", "password": "user1234"}).get_json()
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 3600
    assert data["user"]["role"] == "user"
    assert anon.get("/me", headers={"Authorization": "Bearer " + data["access_token"]}).status_code == 200


def test_requests_without_a_valid_token_are_401(anon, app):
    token = logged_in(app, "nearchos@example.com", "user1234").environ_base["HTTP_AUTHORIZATION"].split()[1]
    cases = [
        ({}, "log in"),
        ({"Authorization": "Bearer not-a-token"}, "Invalid token"),
        ({"Authorization": "Bearer " + token[:-2] + "xx"}, "Invalid token"),
        ({"Authorization": "Token " + token}, "Bearer"),
    ]
    for headers, message in cases:
        response = anon.get("/me", headers=headers)
        assert response.status_code == 401, headers
        assert message in response.get_json()["error"]


def test_expired_token_is_401(app):
    app.config["TOKEN_LIFETIME"] = timedelta(seconds=-1)
    response = logged_in(app, "nearchos@example.com", "user1234").get("/me")
    assert response.status_code == 401
    assert "expired" in response.get_json()["error"]


def test_token_from_another_secret_key_is_rejected(anon, restart):
    other = restart(SECRET_KEY="a-different-secret-key-of-32-bytes-or-more")
    token = logged_in(other, "nearchos@example.com", "user1234").environ_base["HTTP_AUTHORIZATION"]
    assert anon.get("/me", headers={"Authorization": token}).status_code == 401


def test_logout_invalidates_every_token_of_the_user(app, user):
    other_device = logged_in(app, "nearchos@example.com", "user1234")
    assert user.post("/auth/logout").status_code == 200
    assert user.get("/me").status_code == 401
    assert other_device.get("/me").status_code == 401
    # Logging in again works as usual
    assert logged_in(app, "nearchos@example.com", "user1234").get("/me").status_code == 200


def test_public_endpoints_ignore_a_bad_token(anon):
    assert anon.get("/flights/ABC123", headers={"Authorization": "Bearer junk"}).status_code == 200


def test_errors_are_json(anon):
    assert anon.get("/does-not-exist").get_json() is not None
    assert anon.get("/does-not-exist").status_code == 404
    assert anon.put("/flights").status_code == 405


def test_delete_account_cancels_reservations(app, user, anon, passenger):
    response = user.post("/reservations", json={"flight_code": "ABC123", "ticket_class": "economy", "passenger": passenger})
    assert response.status_code == 201
    before = anon.get("/flights/ABC123").get_json()["flight"]["tickets"]["economy"]["available"]

    assert user.delete("/me").status_code == 204
    assert user.get("/me").status_code == 401
    after = anon.get("/flights/ABC123").get_json()["flight"]["tickets"]["economy"]["available"]
    assert after == before + 1
    assert anon.post("/auth/login", json={"email": "nearchos@example.com", "password": "user1234"}).status_code == 401


def test_admin_cannot_delete_own_account(admin):
    assert admin.delete("/me").status_code == 403


def test_admin_password_from_config_applies_to_existing_database(restart):
    restarted = restart(ADMIN_PASSWORD="changed-pass")
    client = restarted.test_client()
    assert client.post("/auth/login", json={"email": "admin@example.com", "password": "changed-pass"}).status_code == 200
    assert client.post("/auth/login", json={"email": "admin@example.com", "password": "admin1234"}).status_code == 401


def test_restart_does_not_duplicate_seed_data(app, restart):
    restart()
    with app.app_context():
        from airline import db

        assert db.users().count_documents({}) == 2
        assert db.flights().count_documents({}) == 3
