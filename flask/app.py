from flask import Flask, Response, session, jsonify, request, redirect, url_for
from pymongo import MongoClient, ReturnDocument
from pymongo.collation import Collation
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os, secrets, random, string, math
from datetime import datetime, date, timedelta

# Connect to MongoDB (docker-compose sets MONGO_URI to the mongodb service)
client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"))


# Choose InfoSys database
db = client["DigitalAirlines"]
users_collection = db["users_collection"]
flights_collection = db["flights_collection"]
reservations_collection = db["reservations_collection"]

# Initiate Flask App
app = Flask(__name__)
# Set SECRET_KEY in production so sessions survive restarts
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

TICKET_CLASSES = ("business", "economy")
DATE_FORMAT = "%d-%m-%Y"
# Compare airport names ignoring case ("london" matches "London")
CASE_INSENSITIVE = Collation(locale="en", strength=2)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

def parse_date(value):
    # Returns a date for a dd-mm-yyyy string, or None if it isn't one
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except (TypeError, ValueError):
        return None

def days_from_now(days):
    return (date.today() + timedelta(days=days)).strftime(DATE_FORMAT)

def normalize_email(email):
    return email.strip().lower() if email else email

def parse_non_negative(value, number_type):
    # Returns the value as int/float, or None if it isn't a finite number >= 0
    try:
        number = number_type(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number

# Initial administrator, sample flights and sample user
initial_admin = {
    "name": "John",
    "surname": "Doe",
    "email": "admin@example.com",
    "password": generate_password_hash(ADMIN_PASSWORD or "admin"),
    "date_of_birth": "01-01-2000",
    "country_of_origin": "Greece",
    "passport_number": "E20113",
    "role": "admin"
}

# Sample flight dates are relative to the first start, so they are always in the future
flight1 = {
    "code": "ABC123",
    "departure_airport": "New York",
    "destination_airport": "London",
    "flight_date": days_from_now(30),
    "business_tickets_available": 50,
    "business_tickets_cost": 800,
    "economy_tickets_available": 100,
    "economy_tickets_cost": 400
}

flight2 = {
    "code": "DEF456",
    "departure_airport": "Los Angeles",
    "destination_airport": "Tokyo",
    "flight_date": days_from_now(45),
    "business_tickets_available": 20,
    "business_tickets_cost": 1200,
    "economy_tickets_available": 150,
    "economy_tickets_cost": 600
}

flight3 = {
    "code": "GHI789",
    "departure_airport": "London",
    "destination_airport": "Paris",
    "flight_date": days_from_now(60),
    "business_tickets_available": 30,
    "business_tickets_cost": 900,
    "economy_tickets_available": 80,
    "economy_tickets_cost": 350
}

user1 = {
    "name": "Nearchos",
    "surname": "Nikolaidis",
    "email": "nearchos@example.com",
    "password": generate_password_hash("12345"),
    "date_of_birth": "06-05-2002",
    "country_of_origin": "Greece",
    "passport_number": "ABC123456",
    "role": "simple"
}

def seed_database():
    users_collection.create_index("email", unique=True)
    flights_collection.create_index("code", unique=True)
    reservations_collection.create_index("reservation_code", unique=True)

    # Only insert the sample documents if they don't exist yet, so restarts don't create duplicates
    for user in [initial_admin, user1]:
        users_collection.update_one({"email": user["email"]}, {"$setOnInsert": user}, upsert=True)
    for flight in [flight1, flight2, flight3]:
        flights_collection.update_one({"code": flight["code"]}, {"$setOnInsert": flight}, upsert=True)

    # Apply ADMIN_PASSWORD on every start, so changing it takes effect on an existing database
    if ADMIN_PASSWORD:
        users_collection.update_one({"email": initial_admin["email"]}, {"$set": {"password": initial_admin["password"]}})

seed_database()

def generate_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return code

def generate_unique_code(collection, field):
    code = generate_code()
    while collection.find_one({field: code}):
        code = generate_code()
    return code

def login_required(role=None):
    # Reject requests without a session, or from the wrong role when one is given
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if 'email' not in session or (role and session.get('role') != role):
                return Response("Unauthorized access."), 401
            return view(*args, **kwargs)
        return wrapper
    return decorator

@app.route("/home")
def home():
    main_urls = [
        "/userRegistration (POST)",
        "/login (POST)"
    ]

    response = {
        "message": "Welcome to Digital Airlines! You have to register first if you are a simple user. If you are an admin you can login. If you want to POST, PUT OR DELETE data you should click Body --> form-data and fill key and value. If you want to GET data you should click Params and fill key and value. Please provide the date in the format dd-mm-yyyy.",
        "main_urls": main_urls
    }

    return jsonify(response)

@app.route("/adminHome")
def adminHome():
    admin_urls = [
        "/createFlight (POST)",
        "/updateTicketsPrice (PUT)",
        "/deleteFlight (DELETE)",
        "/searchFlight (GET)",
        "/flightDetails (GET)",
        "/logout (POST)"
    ]

    response = {
        "message": "Welcome Admin to Digital Airlines! If you want to POST, PUT OR DELETE data you should click Body --> form-data and fill key and value. If you want to GET data you should click Params and fill key and value.  Please provide the date in the format dd-mm-yyyy.",
        "admin_urls": admin_urls
    }

    return jsonify(response)

@app.route("/simpleUserHome")
def simpleUserHome():
    simple_urls = [
        "/searchFlight (GET)",
        "/flightDetails (GET)",
        "/makeReservation (POST)",
        "/displayReservations (GET)",
        "/displayReservationDetails (GET)",
        "/cancelReservation (DELETE)",
        "/deleteAccount (DELETE)",
        "/logout (POST)"
    ]

    response = {
        "message": "Welcome Simple User to Digital Airlines! If you want to POST, PUT OR DELETE data you should click Body --> form-data and fill key and value. If you want to GET data you should click Params and fill key and value.  Please provide the date in the format dd-mm-yyyy.",
        "simple_user_urls": simple_urls
    }

    return jsonify(response)

@app.route("/userRegistration", methods=["POST"])
def user_registration():
    user_data = {
        "name": request.form.get("name"),
        "surname": request.form.get("surname"),
        "email": normalize_email(request.form.get("email")),
        "password": request.form.get("password"),
        "date_of_birth": request.form.get("date_of_birth"),
        "country_of_origin": request.form.get("country_of_origin"),
        "passport_number": request.form.get("passport_number"),
        "role": "simple"
    }

    if not all(user_data.values()):
        return Response("Incomplete data was given"), 400

    date_of_birth = parse_date(user_data["date_of_birth"])
    if not date_of_birth:
        return Response("Invalid date format. Please provide the date of birth in the format dd-mm-yyyy."), 400
    user_data["date_of_birth"] = date_of_birth.strftime(DATE_FORMAT)

    # Check if user with the same email already exists
    if users_collection.find_one({"email": user_data["email"]}):
        return Response("User with the same email already exists"), 400

    user_data["password"] = generate_password_hash(user_data["password"])
    users_collection.insert_one(user_data)
    return Response("User registration successful with the given email: {}".format(user_data["email"])), 200

@app.route("/login", methods=["POST"])
def login():
    email = normalize_email(request.form.get("email"))
    password = request.form.get("password")

    user = users_collection.find_one({'email': email})

    if not user or not password or not check_password_hash(user['password'], password):
        return Response("Wrong email or password."), 401

    session['email'] = email
    session['role'] = user['role']
    session.permanent = True

    if user['role'] == 'admin':
        return redirect(url_for('adminHome'))
    return redirect(url_for('simpleUserHome'))

@app.route("/createFlight", methods=["POST"]) # admin
@login_required(role="admin")
def createFlight():
    fields = ["departure_airport", "destination_airport", "flight_date", "business_tickets_available", "business_tickets_cost", "economy_tickets_available", "economy_tickets_cost"]
    if not all(request.form.get(field) for field in fields):
        return Response("Incomplete data was given"), 400

    flight_date = parse_date(request.form.get("flight_date"))
    if not flight_date:
        return Response("Invalid date format. Please provide the date in the format dd-mm-yyyy."), 400
    if flight_date < date.today():
        return Response("The flight date can't be in the past."), 400

    tickets_and_costs = {
        "business_tickets_available": parse_non_negative(request.form.get("business_tickets_available"), int),
        "business_tickets_cost": parse_non_negative(request.form.get("business_tickets_cost"), float),
        "economy_tickets_available": parse_non_negative(request.form.get("economy_tickets_available"), int),
        "economy_tickets_cost": parse_non_negative(request.form.get("economy_tickets_cost"), float)
    }
    if None in tickets_and_costs.values():
        return Response("Ticket availability must be whole numbers and ticket costs must be numbers, and neither can be negative."), 400

    flight_data = {
        "code": generate_unique_code(flights_collection, "code"),
        "departure_airport": request.form.get("departure_airport").strip(),
        "destination_airport": request.form.get("destination_airport").strip(),
        "flight_date": flight_date.strftime(DATE_FORMAT),
        **tickets_and_costs
    }

    flights_collection.insert_one(flight_data)
    return Response("The flight(code: {}) with departure from {} and destination to {} was added to the MongoDB".format(flight_data['code'], flight_data['departure_airport'], flight_data['destination_airport'])), 200

@app.route("/updateTicketsPrice", methods=["PUT"]) # admin
@login_required(role="admin")
def updateTicketsPrice():
    flight_code = request.form.get("flight_code")
    new_business_tickets_cost = request.form.get("new_business_tickets_cost")
    new_economy_tickets_cost = request.form.get("new_economy_tickets_cost")

    if not all([flight_code, new_business_tickets_cost, new_economy_tickets_cost]):
        return Response("Incomplete data provided"), 400

    new_business_tickets_cost = parse_non_negative(new_business_tickets_cost, float)
    new_economy_tickets_cost = parse_non_negative(new_economy_tickets_cost, float)
    if new_business_tickets_cost is None or new_economy_tickets_cost is None:
        return Response("Ticket costs must be numbers and can't be negative."), 400

    # Update the flight ticket prices in the database
    flight = flights_collection.find_one_and_update(
        {"code": flight_code},
        {
            "$set": {
                "business_tickets_cost": new_business_tickets_cost,
                "economy_tickets_cost": new_economy_tickets_cost
            }
        },
        return_document=ReturnDocument.AFTER
    )

    if not flight:
        return Response("Flight not found"), 404

    flight_data = {
        "departure_airport": flight["departure_airport"],
        "destination_airport": flight["destination_airport"],
        "flight_date": flight["flight_date"],
        "business_tickets_available": flight["business_tickets_available"],
        "business_tickets_cost": flight["business_tickets_cost"],
        "economy_tickets_available": flight["economy_tickets_available"],
        "economy_tickets_cost": flight["economy_tickets_cost"]
    }
    return jsonify({"message": "Ticket prices updated for flight {}".format(flight_code), "flight": flight_data}), 200

@app.route("/deleteFlight", methods=["DELETE"]) # admin
@login_required(role="admin")
def deleteFlight():
    flight_code = request.form.get("flight_code")

    flight = flights_collection.find_one({"code": flight_code})

    if flight:
        reservations = reservations_collection.find_one({"flight_code": flight_code})

        if reservations:
            return Response("Flight cannot be deleted as there are existing reservations."), 403
        else:
            flights_collection.delete_one({"code": flight_code})
            return Response("Flight deleted successfully."), 200
    else:
        return Response("Flight not found."), 404

@app.route("/makeReservation", methods=["POST"]) # simple
@login_required(role="simple")
def makeReservation():
    flight_code = request.form.get("flight_code")
    reservation_data = {
        "first_name": request.form.get("first_name"),
        "last_name": request.form.get("last_name"),
        "passport_number": request.form.get("passport_number"),
        "date_of_birth": request.form.get("date_of_birth"),
        "email": request.form.get("email"),
        "ticket_class": request.form.get("ticket_class")
    }

    if not all(reservation_data.values()):
        return Response("Incomplete passenger information."), 400

    date_of_birth = parse_date(reservation_data["date_of_birth"])
    if not date_of_birth:
        return Response("Invalid date format. Please provide the date in the format dd-mm-yyyy."), 400
    reservation_data["date_of_birth"] = date_of_birth.strftime(DATE_FORMAT)

    ticket_class = reservation_data['ticket_class']
    if ticket_class not in TICKET_CLASSES:
        return Response("There isn't such a ticket class."), 400

    flight = flights_collection.find_one({"code": flight_code})
    if not flight:
        return Response("Flight not found."), 404

    flight_date = parse_date(flight["flight_date"])
    if flight_date and flight_date < date.today():
        return Response("This flight has already departed."), 400

    # Reduce available ticket count, only if there is a ticket left (atomic check-and-decrement)
    available_field = "{}_tickets_available".format(ticket_class)
    flight = flights_collection.find_one_and_update(
        {"code": flight_code, available_field: {"$gt": 0}},
        {"$inc": {available_field: -1}}
    )
    if not flight:
        return Response("No {} class tickets available for this flight.".format(ticket_class)), 400

    # Save reservation details
    reservation_code = generate_unique_code(reservations_collection, "reservation_code")
    reservations_collection.insert_one({
        "reservation_code": reservation_code,
        "flight_code": flight_code,
        "user_email": session['email'],
        "reservation_data": reservation_data
    })

    return Response("Ticket booked successfully for flight {} in {}. Reservation code: {}".format(flight_code, ticket_class, reservation_code)), 200

@app.route("/displayReservations", methods=["GET"]) # simple
@login_required(role="simple")
def displayReservations():
    user_email = session['email']
    reservations = reservations_collection.find({"user_email": user_email})

    response = {
        'user_email': user_email,
        'reservations': []
    }
    for reservation in reservations:
        reservation_data = reservation["reservation_data"]
        reservation_details = {
            "reservation_code": reservation["reservation_code"],
            "flight_code": reservation["flight_code"],
            "passenger_name": reservation_data["first_name"] + " " + reservation_data["last_name"],
            "passport_number": reservation_data["passport_number"],
            "date_of_birth": reservation_data["date_of_birth"],
            "email": reservation_data["email"],
            "ticket_class": reservation_data["ticket_class"]
        }

        response["reservations"].append(reservation_details)

    if not response["reservations"]:
        return Response("No reservations found for the user with email: {}".format(user_email)), 404
    return jsonify(response), 200

@app.route("/displayReservationDetails", methods=["GET"]) # simple
@login_required(role="simple")
def displayReservationDetails():
    reservation_code = request.args.get("reservation_code")
    if not reservation_code:
        return Response("Missing query parameter: reservation_code"), 400

    reservation = reservations_collection.find_one({"reservation_code": reservation_code, "user_email": session['email']})

    if not reservation:
        return Response("Reservation not found."), 404
    else:
        flight = flights_collection.find_one({"code": reservation["flight_code"]})

        if not flight:
            return Response("Flight not found."), 404
        else:
            reservation_data = reservation["reservation_data"]
            reservation_details = {
                "reservation_code": reservation["reservation_code"],
                "flight_code": reservation["flight_code"],
                "departure_airport": flight["departure_airport"],
                "destination_airport": flight["destination_airport"],
                "flight_date": flight["flight_date"],
                "passenger_name": reservation_data["first_name"] + " " + reservation_data["last_name"],
                "passport_number": reservation_data["passport_number"],
                "date_of_birth": reservation_data["date_of_birth"],
                "email": reservation_data["email"],
                "ticket_class": reservation_data["ticket_class"]
            }

            return jsonify(reservation_details), 200

def release_reservation(reservation):
    # Give the ticket back to the flight and delete the reservation
    ticket_class = reservation["reservation_data"]["ticket_class"]
    flights_collection.update_one({"code": reservation["flight_code"]}, {"$inc": {"{}_tickets_available".format(ticket_class): 1}})
    reservations_collection.delete_one({"_id": reservation["_id"]})

@app.route("/cancelReservation", methods=["DELETE"]) # simple
@login_required(role="simple")
def cancelReservation():
    reservation_code = request.args.get("reservation_code")
    if not reservation_code:
        return Response("Missing query parameter: reservation_code"), 400

    reservation = reservations_collection.find_one({"reservation_code": reservation_code, "user_email": session['email']})

    if not reservation:
        return Response("Reservation not found."), 404

    release_reservation(reservation)
    return Response("Reservation with code {} has been canceled.".format(reservation_code)), 200

@app.route("/deleteAccount", methods=["DELETE"]) # simple
@login_required(role="simple")
def deleteAccount():
    user_email = session['email']

    # Cancel the user's reservations so their tickets become available again
    for reservation in reservations_collection.find({"user_email": user_email}):
        release_reservation(reservation)

    # Delete the user account
    users_collection.delete_one({"email": user_email})

    # Clear the session
    session.clear()

    return Response("Account deleted successfully for user {}.".format(user_email)), 200

# Query parameters each search type needs
SEARCH_QUERY_PARAMS = {
    "by_airports": ["departure_airport", "destination_airport"],
    "by_airports_and_date": ["departure_airport", "destination_airport", "flight_date"],
    "by_date": ["flight_date"],
    "all": []
}

@app.route("/searchFlight", methods=["GET"]) # admin and simple
@login_required()
def searchFlight():
    query_type = request.args.get("query_type")

    if query_type not in SEARCH_QUERY_PARAMS:
        return Response("Invalid query type. Use one of: {}  (ex: http://localhost:5000/searchFlight?query_type=all)".format(", ".join(SEARCH_QUERY_PARAMS))), 400

    query = {}
    missing = []
    for param in SEARCH_QUERY_PARAMS[query_type]:
        value = (request.args.get(param) or "").strip()
        if not value:
            missing.append(param)
        query[param] = value

    if missing:
        return Response("Missing query parameter(s) for {}: {}".format(query_type, ", ".join(missing))), 400

    if "flight_date" in query:
        # Normalize the date, so 5-7-2026 finds flights stored as 05-07-2026
        flight_date = parse_date(query["flight_date"])
        if not flight_date:
            return Response("Invalid date format. Please provide the date in the format dd-mm-yyyy."), 400
        query["flight_date"] = flight_date.strftime(DATE_FORMAT)

    flights = flights_collection.find(query, collation=CASE_INSENSITIVE)

    flight_list = []
    for flight in flights:
        flight_info = {
            "flight_code": flight["code"],
            "flight_date": flight["flight_date"],
            "departure_airport": flight["departure_airport"],
            "destination_airport": flight["destination_airport"]
        }
        flight_list.append(flight_info)

    response = {
        "message": "Flight search results:",
        "flights": flight_list
    }

    return jsonify(response), 200

@app.route("/flightDetails", methods=["GET"]) # admin and simple
@login_required()
def flightDetails():
    flight_code = request.args.get("flight_code")
    if not flight_code:
        return Response("Missing query parameter: flight_code  (ex: http://localhost:5000/flightDetails?flight_code=xxxxxx)"), 400

    flight = flights_collection.find_one({"code": flight_code})

    if flight:
        # Retrieve flight details
        departure_airport = flight["departure_airport"]
        destination_airport = flight["destination_airport"]
        total_tickets = int(flight["economy_tickets_available"]) + int(flight["business_tickets_available"])
        total_economy_tickets = int(flight["economy_tickets_available"])
        total_business_tickets = int(flight["business_tickets_available"])
        economy_ticket_cost = float(flight["economy_tickets_cost"])
        business_ticket_cost = float(flight["business_tickets_cost"])

        # Retrieve reservations for the flight
        reservations = reservations_collection.find({"flight_code": flight_code})

        # Prepare flight details JSON object
        flight_details = {
            "flight_code": flight_code,
            "departure_airport": departure_airport,
            "destination_airport": destination_airport,
            "total_tickets": total_tickets,
            "total_economy_tickets": total_economy_tickets,
            "total_business_tickets": total_business_tickets,
            "economy_ticket_cost": economy_ticket_cost,
            "business_ticket_cost": business_ticket_cost,
            "reservations": []
        }

        # Prepare reservations JSON objects
        for reservation in reservations:
            reservation_data = reservation["reservation_data"]
            reservation_details = {
                "passenger_name": reservation_data["first_name"] + " " + reservation_data["last_name"],
                "ticket_class": reservation_data["ticket_class"]
            }

            flight_details["reservations"].append(reservation_details)

        return jsonify(flight_details), 200

    else:
        return Response("Flight not found. (http://localhost:5000/flightDetails?flight_code=xxxxxx)"), 404

@app.route("/logout", methods=["GET", "POST"])
def logout():
    if 'email' in session:
        email = session['email']
        session.pop('email', None)
        session.pop('role', None)
        return Response("Logged out successfully for user {}.".format(email)), 200
    else:
        return Response("No active session."), 401


if __name__ == "__main__":
    app.run(host = "0.0.0.0", debug = os.environ.get("FLASK_DEBUG") == "1", port = 5000)
