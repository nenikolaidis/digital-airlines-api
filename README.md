# Digital Airlines(University Project)

Digital Airlines is an online application built using Flask and MongoDB. It allows users to register, search for flights, make bookings, and perform other related actions, which are described in detail below.

## Running the Application

### Administrator

An administrator has the following capabilities:

- **Create a flight:** The administrator can create a new flight by providing required details such as departure airport, destination airport, flight date, ticket availability, and ticket price.

- **Update ticket prices:** The administrator can update the ticket prices for a specific flight.

- **Delete a flight:** The administrator can delete a flight from the system. However, a flight cannot be deleted if there are existing bookings associated with it.

- **Search for a flight:** The administrator can search for flights based on criteria such as departure airport, destination airport, and flight date.

- **View flight details:** The administrator can view the details of a specific flight, including available tickets and their costs.

- **Logout:** The administrator can log out of the system.

### Regular User

A regular user has the following capabilities:

- **Search for a flight:** The user can search for flights based on criteria such as departure airport, destination airport, and flight date.

- **View flight details:** The user can view the details of a specific flight, including available tickets and their costs.

- **Make a booking:** The user can make a booking for a specific flight by providing the required passenger information.

- **View bookings:** The user can see their existing bookings.

- **View booking details:** The user can view details of a specific booking.

- **Cancel a booking:** The user can cancel a specific booking.

- **Delete account:** The user can delete their account from the system.

- **Logout:** The user can log out of the system.

## Running the Program

To run the Digital Airlines application, follow these steps:

1. Install Python on your system.

2. Install the required Python packages by running the following command: `pip install -r requirements.txt`

3. Make sure MongoDB is installed and running on your system.

4. Open a terminal or command prompt and navigate to the project directory.

5. Start the Flask server by running: `python app.py`

6. Once the server is running, access the Digital Airlines application in your web browser by visiting: `http://localhost:5000/home`

7. Follow the provided URLs and endpoints to interact with the application as either an administrator or a regular user.

**Note:** An initial admin account has already been created with the following credentials:

- Email: `admin@example.com`
- Password: `admin`

Enjoy using the Digital Airlines application!

---

## Sample Requests and Responses

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


  
