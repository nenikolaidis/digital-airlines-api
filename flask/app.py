from flask import Flask, Response, session, jsonify, request, redirect, url_for
from pymongo import MongoClient, ReturnDocument
from werkzeug.security import generate_password_hash, check_password_hash
import os, secrets, random, string
from datetime import datetime

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

# Initial administrator, sample flights and sample user
initial_admin = {
    "name": "John",
    "surname": "Doe",
    "email": "admin@example.com",
    "password": generate_password_hash(os.environ.get("ADMIN_PASSWORD", "admin")),
    "date_of_birth": "01-01-2000",
    "country_of_origin": "Greece",
    "passport_number": "E20113",
    "role": "admin"
}

flight1 = {
    "code": "ABC123",
    "departure_airport": "New York",
    "destination_airport": "London",
    "flight_date": "25-06-2023",
    "business_tickets_available": 50,
    "business_tickets_cost": 800,
    "economy_tickets_available": 100,
    "economy_tickets_cost": 400
}

flight2 = {
    "code": "DEF456",
    "departure_airport": "Los Angeles",
    "destination_airport": "Tokyo",
    "flight_date": "30-06-2023",
    "business_tickets_available": 20,
    "business_tickets_cost": 1200,
    "economy_tickets_available": 150,
    "economy_tickets_cost": 600
}

flight3 = {
    "code": "GHI789",
    "departure_airport": "London",
    "destination_airport": "Paris",
    "flight_date": "12-07-2023",
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

seed_database()

def generate_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return code

def generate_unique_code(collection, field):
    code = generate_code()
    while collection.find_one({field: code}):
        code = generate_code()
    return code

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
        "email": request.form.get("email"),
        "password": request.form.get("password"),
        "date_of_birth": request.form.get("date_of_birth"),
        "country_of_origin": request.form.get("country_of_origin"),
        "passport_number": request.form.get("passport_number"),
        "role": "simple"
    }

    if not all(user_data.values()):
        return Response("Incomplete data was given"), 400

    try:
        user_data["date_of_birth"] = datetime.strptime(user_data["date_of_birth"], "%d-%m-%Y").strftime("%d-%m-%Y")
    except ValueError:
        return Response("Invalid date format. Please provide the date of birth in the format dd-mm-yyyy."), 400

    # Check if user with the same email already exists
    if users_collection.find_one({"email": user_data["email"]}):
        return Response("User with the same email already exists"), 400

    user_data["password"] = generate_password_hash(user_data["password"])
    users_collection.insert_one(user_data)
    return Response("User registration successful with the given email: {}".format(user_data["email"])), 200

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
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
def createFlight():
    if 'email' in session and session['role'] == 'admin':
        fields = ["departure_airport", "destination_airport", "flight_date", "business_tickets_available", "business_tickets_cost", "economy_tickets_available", "economy_tickets_cost"]
        if not all(request.form.get(field) for field in fields):
            return Response("Incomplete data was given"), 400

        try:
            flight_date = datetime.strptime(request.form.get("flight_date"), "%d-%m-%Y").strftime("%d-%m-%Y")
        except ValueError:
            return Response("Invalid date format. Please provide the date in the format dd-mm-yyyy."), 400

        try:
            flight_data = {
                "code": generate_unique_code(flights_collection, "code"),
                "departure_airport": request.form.get("departure_airport"),
                "destination_airport": request.form.get("destination_airport"),
                "flight_date": flight_date,
                "business_tickets_available": int(request.form.get("business_tickets_available")),
                "business_tickets_cost": float(request.form.get("business_tickets_cost")),
                "economy_tickets_available": int(request.form.get("economy_tickets_available")),
                "economy_tickets_cost": float(request.form.get("economy_tickets_cost"))
            }
        except ValueError:
            return Response("Ticket availability must be whole numbers and ticket costs must be numbers."), 400

        flights_collection.insert_one(flight_data)
        return Response("The flight(code: {}) with departure from {} and destination to {} was added to the MongoDB".format(flight_data['code'], flight_data['departure_airport'], flight_data['destination_airport'])), 200

    else:
        return Response("Unauthorized access."), 401

@app.route("/updateTicketsPrice", methods=["PUT"]) # admin
def updateTicketsPrice():
    if 'email' in session and session['role'] == 'admin':
        flight_code = request.form.get("flight_code")
        new_business_tickets_cost = request.form.get("new_business_tickets_cost")
        new_economy_tickets_cost = request.form.get("new_economy_tickets_cost")

        if not all([flight_code, new_business_tickets_cost, new_economy_tickets_cost]):
            return Response("Incomplete data provided"), 400

        try:
            new_business_tickets_cost = float(new_business_tickets_cost)
            new_economy_tickets_cost = float(new_economy_tickets_cost)
        except ValueError:
            return Response("Ticket costs must be numbers."), 400

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

    else:
        return Response("Unauthorized access."), 401

@app.route("/deleteFlight", methods=["DELETE"]) # admin
def deleteFlight():
    if 'email' in session and session['role'] == 'admin':
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
    else:
        return Response("Unauthorized access."), 401

@app.route("/makeReservation", methods=["POST"]) # simple
def makeReservation():
    if 'email' in session and session['role'] == 'simple':
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

        try:
            reservation_data["date_of_birth"] = datetime.strptime(reservation_data["date_of_birth"], "%d-%m-%Y").strftime("%d-%m-%Y")
        except ValueError:
            return Response("Invalid date format. Please provide the date in the format dd-mm-yyyy."), 400

        ticket_class = reservation_data['ticket_class']
        if ticket_class not in TICKET_CLASSES:
            return Response("There isn't such a ticket class."), 400

        if not flights_collection.find_one({"code": flight_code}):
            return Response("Flight not found."), 404

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

    else:
        return Response("Unauthorized access."), 401

@app.route("/displayReservations", methods=["GET"]) # simple
def displayReservations():
    if 'email' in session and session['role'] == 'simple':
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

    else:
        return Response("Unauthorized access."), 401

@app.route("/displayReservationDetails", methods=["GET"]) # simple
def displayReservationDetails():
    if 'email' in session and session['role'] == 'simple':
        reservation_code = request.args.get("reservation_code")
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

    else:
        return Response("Unauthorized access."), 401

def release_reservation(reservation):
    # Give the ticket back to the flight and delete the reservation
    ticket_class = reservation["reservation_data"]["ticket_class"]
    flights_collection.update_one({"code": reservation["flight_code"]}, {"$inc": {"{}_tickets_available".format(ticket_class): 1}})
    reservations_collection.delete_one({"_id": reservation["_id"]})

@app.route("/cancelReservation", methods=["DELETE"]) # simple
def cancelReservation():
    if 'email' in session and session['role'] == 'simple':
        reservation_code = request.args.get("reservation_code")
        reservation = reservations_collection.find_one({"reservation_code": reservation_code, "user_email": session['email']})

        if not reservation:
            return Response("Reservation not found."), 404

        release_reservation(reservation)
        return Response("Reservation with code {} has been canceled.".format(reservation_code)), 200

    else:
        return Response("Unauthorized access."), 401

@app.route("/deleteAccount", methods=["DELETE"]) # simple
def deleteAccount():
    if 'email' in session and session['role'] == 'simple':
        user_email = session['email']

        # Cancel the user's reservations so their tickets become available again
        for reservation in reservations_collection.find({"user_email": user_email}):
            release_reservation(reservation)

        # Delete the user account
        users_collection.delete_one({"email": user_email})

        # Clear the session
        session.clear()

        return Response("Account deleted successfully for user {}.".format(user_email)), 200

    else:
        return Response("Unauthorized access."), 401

@app.route("/searchFlight", methods=["GET"]) # admin and simple
def searchFlight():
    if 'email' in session:
        query_type = request.args.get("query_type")

        if query_type == "by_airports":
            # Search based on departure airport and destination airport
            departure_airport = request.args.get("departure_airport")
            destination_airport = request.args.get("destination_airport")
            flights = flights_collection.find({
                "departure_airport": departure_airport,
                "destination_airport": destination_airport
            })

        elif query_type == "by_airports_and_date":
            # Search based on departure airport, destination airport, and flight date
            departure_airport = request.args.get("departure_airport")
            destination_airport = request.args.get("destination_airport")
            flight_date = request.args.get("flight_date")
            flights = flights_collection.find({
                "departure_airport": departure_airport,
                "destination_airport": destination_airport,
                "flight_date": flight_date
            })

        elif query_type == "by_date":
            # Search based on flight date
            flight_date = request.args.get("flight_date")
            flights = flights_collection.find({
                "flight_date": flight_date
            })

        elif query_type == "all":
            # Retrieve all available flights
            flights = flights_collection.find()

        else:
            return Response("Invalid query type.  (ex: http://localhost:5000/searchFlight?query_type=all)"), 400

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

    else:
        return Response("Unauthorized access."), 401

@app.route("/flightDetails", methods=["GET"]) # admin and simple
def flightDetails():
    if 'email' in session:
        flight_code = request.args.get("flight_code")
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

    else:
        return Response("Unauthorized access."), 401

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
