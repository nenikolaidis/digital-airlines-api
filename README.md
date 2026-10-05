# Digital Airlines

A REST API for a small airline booking system, built with **Flask** and **MongoDB** and packaged with **Docker Compose**. Originally a university project. Users can register, search flights and book or cancel tickets, and administrators can manage flights and prices.

## Tech stack

- Python 3.12 / Flask 3
- MongoDB 7 (via PyMongo)
- Docker & Docker Compose

## Quick start

```bash
git clone https://github.com/nenikolaidis/digital-airlines-api.git
cd digital-airlines-api
docker compose up --build
```

The API is then available at <http://localhost:5000/home>. Use Postman or `curl` to interact with it. `POST`/`PUT`/`DELETE` endpoints take **form-data**, and `GET` endpoints take **query parameters**. Dates use the format `dd-mm-yyyy`. Emails and airport names are case-insensitive.

Example with `curl`:

```bash
# log in as the demo user (the session cookie is stored in cookies.txt)
curl -c cookies.txt -X POST -F email=nearchos@example.com -F password=12345 http://localhost:5000/login

# list all flights
curl -b cookies.txt "http://localhost:5000/searchFlight?query_type=all"
```

### Demo accounts

On first start, the database is seeded with two accounts and three sample flights dated 30, 45 and 60 days ahead:

| Role  | Email                  | Password                      |
|-------|------------------------|-------------------------------|
| Admin | `admin@example.com`    | `admin` (or `$ADMIN_PASSWORD`) |
| User  | `nearchos@example.com` | `12345`                       |

### Configuration

| Variable         | Default (docker-compose)    | Description                                          |
|------------------|-----------------------------|------------------------------------------------------|
| `MONGO_URI`      | `mongodb://mongodb:27017`   | MongoDB connection string                            |
| `SECRET_KEY`     | `change-me-in-production`   | Flask session signing key                            |
| `ADMIN_PASSWORD` | `admin`                     | Password for the seeded admin account, applied on every start |
| `FLASK_DEBUG`    | unset                       | Set to `1` to enable Flask debug mode (only with `python app.py`) |

In Docker the API runs under gunicorn as a non-root user. MongoDB is not published to the host, so only the API container can reach it.

### Running without Docker

Requires Python 3.10+ and a MongoDB instance running on `localhost:27017`.

```bash
cd flask
pip install -r requirements.txt
python app.py
```

## API

### Public

| Method | Endpoint            | Description                                                                 |
|--------|---------------------|-----------------------------------------------------------------------------|
| GET    | `/home`             | Welcome message and available endpoints                                     |
| POST   | `/userRegistration` | `name`, `surname`, `email`, `password`, `date_of_birth`, `country_of_origin`, `passport_number` |
| POST   | `/login`            | `email`, `password`; redirects to the admin or user home                    |
| POST   | `/logout`           | Ends the session                                                            |

### Admin

| Method | Endpoint              | Description                                                                 |
|--------|-----------------------|-----------------------------------------------------------------------------|
| POST   | `/createFlight`       | `departure_airport`, `destination_airport`, `flight_date`, `business_tickets_available`, `business_tickets_cost`, `economy_tickets_available`, `economy_tickets_cost` |
| PUT    | `/updateTicketsPrice` | `flight_code`, `new_business_tickets_cost`, `new_economy_tickets_cost`      |
| DELETE | `/deleteFlight`       | `flight_code`; refused if the flight has reservations                       |

### User

| Method | Endpoint                     | Description                                                          |
|--------|------------------------------|----------------------------------------------------------------------|
| POST   | `/makeReservation`           | `flight_code`, `first_name`, `last_name`, `passport_number`, `date_of_birth`, `email`, `ticket_class` (`business`/`economy`); returns a reservation code |
| GET    | `/displayReservations`       | Your reservations                                                    |
| GET    | `/displayReservationDetails` | `reservation_code`                                                   |
| DELETE | `/cancelReservation`         | `reservation_code`; the ticket becomes available again               |
| DELETE | `/deleteAccount`             | Deletes your account and cancels your reservations                   |

### Admin & user

| Method | Endpoint         | Description                                                                 |
|--------|------------------|-----------------------------------------------------------------------------|
| GET    | `/searchFlight`  | `query_type` = `all`, `by_date` (`flight_date`), `by_airports` (`departure_airport`, `destination_airport`) or `by_airports_and_date` |
| GET    | `/flightDetails` | `flight_code`; availability, prices and passenger list                     |

---

## Screenshots

> These screenshots are from the original version of the project, so some response formats differ slightly from the current API.

1. When opening the application, you will land on the Home Page. From there, you can either register as a user or log in.

2. After login
   
### Admin

- Admin Home

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/e44231c1-d47b-410e-a7d8-f6a076794fe0)

- Create Flight

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/fd1bb2f2-5580-412e-ae73-450eba72da9f)

- Update Ticket Price

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/dc021bcd-c7d8-452a-ac5b-d4b235f28963)

- Delete Flight

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/1f4ec61a-2c3e-4fcc-99dd-03405c830eb5)

3. After User Registration

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/cc9de386-c76f-45be-a3c8-7093733bd68c)


### Regular user

- Simple User Home

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/51650538-9902-4f79-8cec-0c58055759c0)

- Make Reservation

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/db6ca3e8-1365-4744-9ce3-24a41b800830)

- Display Reservations

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/9a2b5bb1-893c-43fe-a37f-cbd3781cfb60)

-  Display Reservation Details
  
![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/b6bceb3a-eafe-488a-abd4-d93e004ab7f1)

-  Cancel Reservation

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/5daab495-02a1-429f-b234-8aa6ce27aefb)

-  Delete Account

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/6d1ba60a-c860-4567-a909-4b80debbc300)


4. Common procedures for both users

- Search Flight

all

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/389b50ab-5455-4d50-99e4-0c9ed0659165)

by_date

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/8c144151-99d8-456f-bc5e-cee5199cd5c2)

-Flight Details

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/753c5dd4-3024-40ef-ab46-bafc6d6be7e6)

- Logout

![image](https://github.com/nenikolaidis/YpoxreotikiErgasia23_e20113_Nikolaidis_Nearchos/assets/129533209/b09e41b0-8fb0-4728-9e8d-43df57fa9dd8)


  
