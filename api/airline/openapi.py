"""OpenAPI description of the API, served at /openapi.json and rendered by Swagger UI at /docs."""

import re

from .pagination import DEFAULT_PER_PAGE, MAX_PER_PAGE
from .validation import TICKET_CLASSES


def openapi_path(flask_rule):
    """/flights/<code> -> /flights/{code}"""
    return re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", flask_rule)


def ref(name):
    return {"$ref": f"#/components/schemas/{name}"}


def json_content(schema):
    return {"application/json": {"schema": schema}}


def ok(description, schema=None, status="200"):
    response = {"description": description}
    if schema:
        response["content"] = json_content(schema)
    return {status: response}


def errors(*statuses):
    descriptions = {
        "400": "Invalid input",
        "401": "Not logged in, or wrong credentials",
        "403": "Logged in with the wrong role",
        "404": "Not found",
        "409": "Conflicts with the current state",
    }
    return {status: {"description": descriptions[status], "content": json_content(ref("Error"))} for status in statuses}


def body(schema):
    return {"required": True, "content": json_content(schema)}


def code_param(description):
    return {"name": "code", "in": "path", "required": True, "description": description, "schema": {"type": "string", "example": "ABC123"}}


BEARER = [{"bearerAuth": []}]

PAGE_PARAMETERS = [
    {"name": "page", "in": "query", "description": "Page number", "schema": {"type": "integer", "minimum": 1, "default": 1}},
    {
        "name": "per_page",
        "in": "query",
        "description": "Results per page",
        "schema": {"type": "integer", "minimum": 1, "maximum": MAX_PER_PAGE, "default": DEFAULT_PER_PAGE},
    },
]


def page_of(field, item_schema):
    return {
        "type": "object",
        "properties": {
            "page": {"type": "integer", "example": 1},
            "per_page": {"type": "integer", "example": DEFAULT_PER_PAGE},
            "total": {"type": "integer", "description": "Results across all pages"},
            "pages": {"type": "integer"},
            "count": {"type": "integer", "description": "Results on this page"},
            field: {"type": "array", "items": item_schema},
        },
    }


def date_query(name, description):
    return {"name": name, "in": "query", "description": description, "schema": {"type": "string", "format": "date"}}


FLIGHT_PROPERTIES = {
    "code": {"type": "string", "example": "ABC123"},
    "departure_airport": {"type": "string", "example": "New York"},
    "destination_airport": {"type": "string", "example": "London"},
    "flight_date": {"type": "string", "format": "date"},
    "tickets": ref("Tickets"),
}

SCHEMAS = {
    "Error": {
        "type": "object",
        "properties": {"error": {"type": "string", "example": "Flight ABC999 not found."}},
        "required": ["error"],
    },
    "Message": {"type": "object", "properties": {"message": {"type": "string"}}},
    "TicketClass": {
        "type": "object",
        "properties": {
            "available": {"type": "integer", "minimum": 0, "example": 100},
            "price": {"type": "number", "minimum": 0, "example": 400},
        },
        "required": ["available", "price"],
    },
    "Tickets": {
        "type": "object",
        "properties": {ticket_class: ref("TicketClass") for ticket_class in TICKET_CLASSES},
        "required": list(TICKET_CLASSES),
    },
    "Flight": {"type": "object", "properties": FLIGHT_PROPERTIES},
    "FlightDetails": {
        "type": "object",
        "properties": {
            **FLIGHT_PROPERTIES,
            "reservations": {
                "description": "Only included for admins",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "reservation_code": {"type": "string"},
                        "passenger_name": {"type": "string"},
                        "ticket_class": {"type": "string", "enum": list(TICKET_CLASSES)},
                    },
                },
            },
        },
    },
    "NewFlight": {
        "type": "object",
        "properties": {
            "departure_airport": {"type": "string", "example": "Athens"},
            "destination_airport": {"type": "string", "example": "Rome"},
            "flight_date": {"type": "string", "format": "date", "description": "Today or later"},
            "tickets": ref("Tickets"),
        },
        "required": ["departure_airport", "destination_airport", "flight_date", "tickets"],
    },
    "PriceUpdate": {
        "type": "object",
        "properties": {
            "tickets": {
                "type": "object",
                "minProperties": 1,
                "properties": {
                    ticket_class: {
                        "type": "object",
                        "properties": {"price": {"type": "number", "minimum": 0}},
                        "required": ["price"],
                        "additionalProperties": False,
                    }
                    for ticket_class in TICKET_CLASSES
                },
                "additionalProperties": False,
            }
        },
        "required": ["tickets"],
        "example": {"tickets": {"economy": {"price": 420}}},
    },
    "User": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "surname": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "date_of_birth": {"type": "string", "format": "date"},
            "country_of_origin": {"type": "string"},
            "passport_number": {"type": "string"},
            "role": {"type": "string", "enum": ["admin", "user"]},
        },
    },
    "Registration": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "example": "Eleni"},
            "surname": {"type": "string", "example": "Georgiou"},
            "email": {"type": "string", "format": "email", "example": "eleni@example.com"},
            "password": {"type": "string", "minLength": 8, "example": "s3cure-pass"},
            "date_of_birth": {"type": "string", "format": "date", "example": "1998-02-01"},
            "country_of_origin": {"type": "string", "example": "Greece"},
            "passport_number": {"type": "string", "example": "K998877"},
        },
        "required": ["name", "surname", "email", "password", "date_of_birth", "country_of_origin", "passport_number"],
    },
    "Login": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "format": "email", "example": "nearchos@example.com"},
            "password": {"type": "string", "example": "user1234"},
        },
        "required": ["email", "password"],
    },
    "LoginResponse": {
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Send it as `Authorization: Bearer <access_token>`"},
            "token_type": {"type": "string", "example": "Bearer"},
            "expires_in": {"type": "integer", "description": "Seconds until the token expires", "example": 3600},
            "user": ref("User"),
        },
    },
    "UserResponse": {
        "type": "object",
        "properties": {"message": {"type": "string"}, "user": ref("User")},
    },
    "Passenger": {
        "type": "object",
        "properties": {
            "first_name": {"type": "string", "example": "Maria"},
            "last_name": {"type": "string", "example": "Papadopoulou"},
            "passport_number": {"type": "string", "example": "AE123456"},
            "date_of_birth": {"type": "string", "format": "date", "example": "1990-04-12"},
            "email": {"type": "string", "format": "email", "example": "maria@example.com"},
        },
        "required": ["first_name", "last_name", "passport_number", "date_of_birth", "email"],
    },
    "NewReservation": {
        "type": "object",
        "properties": {
            "flight_code": {"type": "string", "example": "ABC123"},
            "ticket_class": {"type": "string", "enum": list(TICKET_CLASSES), "example": "economy"},
            "passenger": ref("Passenger"),
        },
        "required": ["flight_code", "ticket_class", "passenger"],
    },
    "Reservation": {
        "type": "object",
        "properties": {
            "reservation_code": {"type": "string", "example": "F7BN6W"},
            "flight_code": {"type": "string", "example": "ABC123"},
            "ticket_class": {"type": "string", "enum": list(TICKET_CLASSES)},
            "price": {"type": "number", "description": "Price paid at booking time"},
            "booked_at": {"type": "string", "format": "date-time"},
            "passenger": ref("Passenger"),
            "flight": {
                "description": "Included when creating or fetching a single reservation",
                "type": "object",
                "properties": {
                    "departure_airport": {"type": "string"},
                    "destination_airport": {"type": "string"},
                    "flight_date": {"type": "string", "format": "date"},
                },
            },
        },
    },
}

PATHS = {
    "/auth/register": {
        "post": {
            "tags": ["Auth"],
            "summary": "Create a user account",
            "requestBody": body(ref("Registration")),
            "responses": {**ok("Account created", ref("UserResponse"), "201"), **errors("400", "409")},
        }
    },
    "/auth/login": {
        "post": {
            "tags": ["Auth"],
            "summary": "Log in and get an access token",
            "description": "Returns a bearer token that is valid for an hour. "
            "In Swagger UI, copy `access_token`, click **Authorize** and paste it. "
            "Demo user: `nearchos@example.com` / `user1234`.",
            "requestBody": body(ref("Login")),
            "responses": {**ok("Logged in", ref("LoginResponse")), **errors("400", "401")},
        }
    },
    "/auth/logout": {
        "post": {
            "tags": ["Auth"],
            "summary": "Log out everywhere",
            "security": BEARER,
            "description": "Requires login. Invalidates every token issued to you so far, on all devices.",
            "responses": {**ok("Logged out", ref("Message")), **errors("401")},
        }
    },
    "/me": {
        "get": {
            "tags": ["Auth"],
            "summary": "Your profile",
            "security": BEARER,
            "description": "Requires login.",
            "responses": {
                **ok("Your profile", {"type": "object", "properties": {"user": ref("User")}}),
                **errors("401"),
            },
        },
        "delete": {
            "tags": ["Auth"],
            "summary": "Delete your account",
            "security": BEARER,
            "description": "Requires a user login. Your reservations are cancelled and their tickets become available again.",
            "responses": {**ok("Account deleted", status="204"), **errors("401", "403")},
        },
    },
    "/flights": {
        "get": {
            "tags": ["Flights"],
            "summary": "Search flights",
            "description": "Public. All filters are optional and can be combined; airport names are case-insensitive.",
            "parameters": [
                {"name": "from", "in": "query", "description": "Departure airport", "schema": {"type": "string"}, "example": "New York"},
                {"name": "to", "in": "query", "description": "Destination airport", "schema": {"type": "string"}, "example": "London"},
                date_query("date", "Exact flight date"),
                date_query("date_from", "Earliest flight date (ignored when date is set)"),
                date_query("date_to", "Latest flight date (ignored when date is set)"),
                *PAGE_PARAMETERS,
            ],
            "responses": {
                **ok(
                    "Matching flights, sorted by date",
                    page_of("flights", ref("Flight")),
                ),
                **errors("400"),
            },
        },
        "post": {
            "tags": ["Flights"],
            "summary": "Create a flight",
            "security": BEARER,
            "description": "Requires an admin login. The flight code is generated.",
            "requestBody": body(ref("NewFlight")),
            "responses": {
                **ok("Flight created", {"type": "object", "properties": {"flight": ref("Flight")}}, "201"),
                **errors("400", "401", "403"),
            },
        },
    },
    "/flights/{code}": {
        "parameters": [code_param("Flight code")],
        "get": {
            "tags": ["Flights"],
            "summary": "Flight details",
            "description": "Public. When called with an admin token, the passenger list is included too.",
            "security": [{}, *BEARER],
            "responses": {
                **ok("The flight", {"type": "object", "properties": {"flight": ref("FlightDetails")}}),
                **errors("404"),
            },
        },
        "patch": {
            "tags": ["Flights"],
            "summary": "Change ticket prices",
            "security": BEARER,
            "description": "Requires an admin login. Availability can't be changed directly; bookings manage it.",
            "requestBody": body(ref("PriceUpdate")),
            "responses": {
                **ok("The updated flight", {"type": "object", "properties": {"flight": ref("Flight")}}),
                **errors("400", "401", "403", "404"),
            },
        },
        "delete": {
            "tags": ["Flights"],
            "summary": "Delete a flight",
            "security": BEARER,
            "description": "Requires an admin login. Refused while the flight has reservations.",
            "responses": {**ok("Flight deleted", status="204"), **errors("401", "403", "404", "409")},
        },
    },
    "/reservations": {
        "get": {
            "tags": ["Reservations"],
            "summary": "Your reservations",
            "security": BEARER,
            "description": "Requires a user login.",
            "parameters": PAGE_PARAMETERS,
            "responses": {
                **ok(
                    "Your reservations, oldest first",
                    page_of("reservations", ref("Reservation")),
                ),
                **errors("401", "403"),
            },
        },
        "post": {
            "tags": ["Reservations"],
            "summary": "Book a ticket",
            "security": BEARER,
            "description": "Requires a user login. Fails with 409 if the class is sold out or the flight has departed.",
            "requestBody": body(ref("NewReservation")),
            "responses": {
                **ok("Ticket booked", {"type": "object", "properties": {"reservation": ref("Reservation")}}, "201"),
                **errors("400", "401", "403", "404", "409"),
            },
        },
    },
    "/reservations/{code}": {
        "parameters": [code_param("Reservation code")],
        "get": {
            "tags": ["Reservations"],
            "summary": "One of your reservations",
            "security": BEARER,
            "description": "Requires a user login.",
            "responses": {
                **ok("The reservation and its flight", {"type": "object", "properties": {"reservation": ref("Reservation")}}),
                **errors("401", "403", "404"),
            },
        },
        "delete": {
            "tags": ["Reservations"],
            "summary": "Cancel a reservation",
            "security": BEARER,
            "description": "Requires a user login. The ticket becomes available again. Departed flights can't be cancelled.",
            "responses": {**ok("Reservation cancelled", status="204"), **errors("401", "403", "404", "409")},
        },
    },
}

SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "Digital Airlines API",
        "version": "3.0.0",
        "description": "Flight booking REST API built with Flask and MongoDB. "
        "To try the protected endpoints, call **POST /auth/login** with the demo user, "
        "then click **Authorize** and paste the `access_token` from the response.",
    },
    "tags": [
        {"name": "Auth", "description": "Accounts and access tokens"},
        {"name": "Flights", "description": "Search flights; admins create, reprice and delete them"},
        {"name": "Reservations", "description": "Book and cancel tickets (users only)"},
    ],
    "paths": PATHS,
    "components": {
        "schemas": SCHEMAS,
        "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
    },
}
