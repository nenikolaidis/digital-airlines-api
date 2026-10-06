import pytest
from conftest import make_app

DEMO_LOGIN = {"email": "nearchos@example.com", "password": "user1234"}


@pytest.fixture
def limited_app():
    app, cleanup = make_app(RATELIMIT_ENABLED=True, LOGIN_RATE_LIMIT="3 per minute", REGISTER_RATE_LIMIT="2 per hour")
    yield app
    cleanup()


def login(client, ip="10.0.0.1", headers=None, password="user1234"):
    return client.post(
        "/auth/login",
        json={**DEMO_LOGIN, "password": password},
        headers=headers or {},
        environ_overrides={"REMOTE_ADDR": ip},
    )


def test_login_is_rate_limited_per_ip(limited_app):
    client = limited_app.test_client()
    assert [login(client, password="wrong").status_code for _ in range(3)] == [401, 401, 401]

    response = login(client)
    assert response.status_code == 429
    assert response.get_json() == {"error": "Too many requests (3 per 1 minute). Try again later."}
    assert int(response.headers["Retry-After"]) > 0

    # Another IP has its own allowance
    assert login(client, ip="10.0.0.2").status_code == 200


def test_register_is_rate_limited(limited_app):
    client = limited_app.test_client()
    statuses = [client.post("/auth/register", json={}).status_code for _ in range(3)]
    assert statuses == [400, 400, 429]


def test_other_endpoints_are_not_limited_by_the_login_limit(limited_app):
    client = limited_app.test_client()
    for _ in range(3):
        login(client)
    assert login(client).status_code == 429
    assert client.get("/flights", environ_overrides={"REMOTE_ADDR": "10.0.0.1"}).status_code == 200


def test_client_ip_header_is_ignored_unless_configured(limited_app):
    client = limited_app.test_client()
    # Without CLIENT_IP_HEADER, a client can't dodge the limit by sending its own header
    for n in range(4):
        response = login(client, headers={"CF-Connecting-IP": f"203.0.113.{n}"})
    assert response.status_code == 429


def test_configured_client_ip_header_identifies_the_client():
    app, cleanup = make_app(RATELIMIT_ENABLED=True, LOGIN_RATE_LIMIT="2 per minute", CLIENT_IP_HEADER="CF-Connecting-IP")
    try:
        client = app.test_client()
        # Every request arrives from the same proxy address, but the header tells the clients apart
        first = [login(client, ip="172.16.0.1", headers={"CF-Connecting-IP": "203.0.113.7"}).status_code for _ in range(3)]
        assert first == [200, 200, 429]
        assert login(client, ip="172.16.0.1", headers={"CF-Connecting-IP": "203.0.113.8"}).status_code == 200
    finally:
        cleanup()
