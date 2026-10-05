# Digital Airlines API

[![CI](https://github.com/nenikolaidis/digital-airlines-api/actions/workflows/ci.yml/badge.svg)](https://github.com/nenikolaidis/digital-airlines-api/actions/workflows/ci.yml)

A JSON REST API for a small airline booking system, built with **Flask** and **MongoDB** and packaged with **Docker Compose**. Anyone can search flights. Registered users can book and cancel tickets, and administrators manage flights and prices.

It started as a university project for the **University of Piraeus** and has since been rebuilt with an app factory and Blueprints, input validation, atomic seat booking, a pytest suite and CI.

## Tech stack

- Python 3.12, Flask 3, gunicorn
- MongoDB 7 (via PyMongo)
- OpenAPI 3.1 spec with Swagger UI
- pytest and ruff, run by GitHub Actions
- Docker and Docker Compose

## Quick start

```bash
git clone https://github.com/nenikolaidis/digital-airlines-api.git
cd digital-airlines-api
docker compose up --build
```

The API runs at <http://localhost:5000>.

**Interactive docs:** open <http://localhost:5000/docs> to browse every endpoint in Swagger UI and try it from the browser. Run `POST /auth/login` with a demo account first, and the other requests then use that session. The OpenAPI spec itself is at `/openapi.json`.

### Demo accounts

On first start, the database is seeded with two accounts and three sample flights dated 30, 45 and 60 days ahead. Sample flights that have departed are moved forward again on the next start, so a long-running demo always has bookable flights.

| Role  | Email                  | Password                           |
|-------|------------------------|------------------------------------|
| Admin | `admin@example.com`    | `admin1234` (or `$ADMIN_PASSWORD`) |
| User  | `nearchos@example.com` | `user1234`                         |

### Try it with curl

Requests and responses are JSON. Logging in sets a session cookie, which `-c`/`-b` store and send back.

```bash
# search flights (no login needed)
curl "http://localhost:5000/flights?from=new%20york&to=london"

# log in as the demo user
curl -c cookies.txt --json '{"email": "nearchos@example.com", "password": "user1234"}' \
  http://localhost:5000/auth/login

# book an economy ticket
curl -b cookies.txt --json '{
  "flight_code": "ABC123",
  "ticket_class": "economy",
  "passenger": {
    "first_name": "Maria", "last_name": "Papadopoulou", "passport_number": "AE123456",
    "date_of_birth": "1990-04-12", "email": "maria@example.com"
  }
}' http://localhost:5000/reservations

# list your reservations
curl -b cookies.txt http://localhost:5000/reservations
```

(`--json` needs curl 7.82 or newer. With an older curl, use `-H "Content-Type: application/json" -d '...'`.)

## API

Dates use the format `YYYY-MM-DD`. Emails and airport names are case-insensitive. Errors always return a JSON body: `{"error": "..."}`.

### Auth

| Method | Endpoint         | Access    | Description |
|--------|------------------|-----------|-------------|
| POST   | `/auth/register` | public    | Body: `name`, `surname`, `email`, `password` (8+ characters), `date_of_birth`, `country_of_origin`, `passport_number` |
| POST   | `/auth/login`    | public    | Body: `email`, `password`. Starts a session |
| POST   | `/auth/logout`   | logged in | Ends the session |
| GET    | `/me`            | logged in | Your profile |
| DELETE | `/me`            | user      | Deletes your account and cancels your reservations |

### Flights

| Method | Endpoint          | Access | Description |
|--------|-------------------|--------|-------------|
| GET    | `/flights`        | public | Optional filters: `from`, `to`, `date`, or a range with `date_from` and `date_to`. Sorted by date |
| GET    | `/flights/<code>` | public | Availability and prices. Admins also see the passenger list |
| POST   | `/flights`        | admin  | Body: `departure_airport`, `destination_airport`, `flight_date`, `tickets` (see below) |
| PATCH  | `/flights/<code>` | admin  | Change prices, for example `{"tickets": {"economy": {"price": 420}}}` |
| DELETE | `/flights/<code>` | admin  | Refused with 409 while the flight has reservations |

`tickets` has one entry per class:

```json
{"business": {"available": 50, "price": 800}, "economy": {"available": 100, "price": 400}}
```

### Reservations

| Method | Endpoint               | Access | Description |
|--------|------------------------|--------|-------------|
| POST   | `/reservations`        | user   | Body: `flight_code`, `ticket_class` (`business` or `economy`), `passenger` (`first_name`, `last_name`, `passport_number`, `date_of_birth`, `email`) |
| GET    | `/reservations`        | user   | Your reservations |
| GET    | `/reservations/<code>` | user   | One of your reservations, with its flight |
| DELETE | `/reservations/<code>` | user   | Cancels it, and the ticket becomes available again |

Each booking gets its own 6-character reservation code and records the price paid. Users only ever see their own reservations. Seats are taken with a single atomic update, so a class can't be overbooked.

## Configuration

| Variable         | Default (docker-compose)  | Description |
|------------------|---------------------------|-------------|
| `MONGO_URI`      | `mongodb://mongodb:27017` | MongoDB connection string |
| `MONGO_DB`       | `DigitalAirlines`         | Database name |
| `SECRET_KEY`     | `change-me-in-production` | Flask session signing key |
| `ADMIN_PASSWORD` | `admin1234`               | Password for the seeded admin account, applied on every start |
| `SESSION_COOKIE_SECURE` | unset              | Set to `true` when served over HTTPS |
| `PORT`           | `5000`                    | Port gunicorn listens on inside the container |

In Docker, the API runs under gunicorn as a non-root user. MongoDB isn't published to the host, so only the API container can reach it.

## Deployment

The repo includes a [Render](https://render.com) Blueprint ([`render.yaml`](render.yaml)) that deploys the Docker image on Render's free plan, with the database on a free [MongoDB Atlas](https://www.mongodb.com/atlas) cluster:

1. In Atlas, create a free cluster and a database user. Under **Network Access**, allow `0.0.0.0/0`, because Render's free plan has no fixed IP. Copy the `mongodb+srv://...` connection string.
2. In Render, choose **New → Blueprint** and select this repository.
3. When asked, set `MONGO_URI` to the Atlas connection string and `ADMIN_PASSWORD` to a private password. `SECRET_KEY` is generated for you.

Render rebuilds on every push to `main`. Free services sleep when idle, so the first request after a while takes up to a minute.

## Development

Requires Python 3.10+ and MongoDB on `localhost:27017`.

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

flask --app airline run --debug   # http://localhost:5000
pytest                            # each test uses its own throwaway database
ruff check . && ruff format --check .
```

Point the tests at another MongoDB with `TEST_MONGO_URI`.

### Project layout

```
api/
├── airline/
│   ├── __init__.py      # create_app(): config, MongoDB, blueprints, seeding
│   ├── auth.py          # register, login, logout, /me
│   ├── flights.py       # flight search and admin management
│   ├── reservations.py  # booking and cancelling
│   ├── access.py        # @login_required(role=...)
│   ├── validation.py    # request parsing and validation helpers
│   ├── errors.py        # JSON error responses
│   ├── openapi.py       # OpenAPI spec (a test checks it matches the routes)
│   ├── docs.py          # /docs (Swagger UI) and /openapi.json
│   ├── db.py            # collection accessors and unique code generation
│   └── seed.py          # indexes and demo data
├── tests/
├── wsgi.py              # gunicorn entry point
└── Dockerfile
```
