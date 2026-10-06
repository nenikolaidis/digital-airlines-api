export type TicketClass = 'business' | 'economy'
export type Role = 'admin' | 'user'

export interface TicketInfo {
  available: number
  price: number
}

export type Tickets = Record<TicketClass, TicketInfo>

export interface FlightPassenger {
  reservation_code: string
  passenger_name: string
  ticket_class: TicketClass
}

export interface Flight {
  code: string
  departure_airport: string
  destination_airport: string
  flight_date: string
  tickets: Tickets
  // Only included for admins
  reservations?: FlightPassenger[]
}

export interface User {
  name: string
  surname: string
  email: string
  date_of_birth: string
  country_of_origin: string
  passport_number: string
  role: Role
}

export interface PageInfo {
  page: number
  per_page: number
  total: number
  pages: number
  count: number
}

export interface Passenger {
  first_name: string
  last_name: string
  passport_number: string
  date_of_birth: string
  email: string
}

export interface Reservation {
  reservation_code: string
  flight_code: string
  ticket_class: TicketClass
  price: number
  booked_at: string
  passenger: Passenger
  flight?: Pick<Flight, 'departure_airport' | 'destination_airport' | 'flight_date'>
}

export interface LoginResponse {
  access_token: string
  token_type: 'Bearer'
  expires_in: number
  user: User
}

export interface Registration {
  name: string
  surname: string
  email: string
  password: string
  date_of_birth: string
  country_of_origin: string
  passport_number: string
}
