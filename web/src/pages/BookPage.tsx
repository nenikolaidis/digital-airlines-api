import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'
import { getFlight } from '../api'
import { useAuth } from '../authContext'
import { formatDate, formatPrice, useSlowNotice } from '../format'
import type { Flight, Passenger, Reservation, TicketClass } from '../types'

const CLASSES: TicketClass[] = ['economy', 'business']

export default function BookPage() {
  const { code = '' } = useParams()
  const [params] = useSearchParams()
  const { user, authRequest } = useAuth()
  const navigate = useNavigate()

  const [flight, setFlight] = useState<Flight | null>(null)
  const [loadError, setLoadError] = useState('')
  const [ticketClass, setTicketClass] = useState<TicketClass>(params.get('class') === 'business' ? 'business' : 'economy')
  // Pre-filled with the logged-in user's details; they can book for someone else by editing them
  const [passenger, setPassenger] = useState<Passenger>({
    first_name: user?.name ?? '',
    last_name: user?.surname ?? '',
    passport_number: user?.passport_number ?? '',
    date_of_birth: user?.date_of_birth ?? '',
    email: user?.email ?? '',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const slow = useSlowNotice(!flight && !loadError)

  useEffect(() => {
    let cancelled = false
    getFlight(code)
      .then(({ flight }) => !cancelled && setFlight(flight))
      .catch((err: Error) => !cancelled && setLoadError(err.message))
    return () => {
      cancelled = true
    }
  }, [code])

  function field(name: keyof Passenger) {
    return {
      value: passenger[name],
      required: true,
      onChange: (e: { target: { value: string } }) => setPassenger({ ...passenger, [name]: e.target.value }),
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const { reservation } = await authRequest<{ reservation: Reservation }>('/reservations', {
        method: 'POST',
        body: { flight_code: code, ticket_class: ticketClass, passenger },
      })
      navigate('/trips', { state: { booked: reservation.reservation_code } })
    } catch (err) {
      setError((err as Error).message)
      setSubmitting(false)
    }
  }

  if (loadError) {
    return (
      <section className="narrow">
        <h1>Flight not available</h1>
        <p className="alert">{loadError}</p>
        <p>
          <Link to="/">Back to search</Link>
        </p>
      </section>
    )
  }
  if (!flight) {
    return <p className="muted">Loading flight…{slow && ' The free demo server is waking up, which can take up to a minute.'}</p>
  }

  const selected = flight.tickets[ticketClass]
  return (
    <section className="narrow">
      <p>
        <Link to="/">← Back to search</Link>
      </p>
      <h1>
        {flight.departure_airport} → {flight.destination_airport}
      </h1>
      <p className="muted">
        {formatDate(flight.flight_date)} · Flight {flight.code}
      </p>

      <form className="card form" onSubmit={handleSubmit}>
        <fieldset className="class-picker">
          <legend>Class</legend>
          {CLASSES.map((option) => {
            const { available, price } = flight.tickets[option]
            return (
              <label key={option} className={`class-option${ticketClass === option ? ' selected' : ''}`}>
                <input
                  type="radio"
                  name="ticket_class"
                  value={option}
                  checked={ticketClass === option}
                  disabled={!available}
                  onChange={() => setTicketClass(option)}
                />
                <span className="fare-class">{option === 'economy' ? 'Economy' : 'Business'}</span>
                <span className="fare-price">{formatPrice(price)}</span>
                <span className={available ? 'muted' : 'sold-out'}>{available ? `${available} seats left` : 'Sold out'}</span>
              </label>
            )
          })}
        </fieldset>

        <h2 className="form-heading">Passenger</h2>
        <div className="form-row">
          <label>
            First name
            <input {...field('first_name')} />
          </label>
          <label>
            Last name
            <input {...field('last_name')} />
          </label>
        </div>
        <div className="form-row">
          <label>
            Passport number
            <input {...field('passport_number')} />
          </label>
          <label>
            Date of birth
            <input type="date" {...field('date_of_birth')} />
          </label>
        </div>
        <label>
          Email
          <input type="email" {...field('email')} />
        </label>

        {error && <p className="alert">{error}</p>}
        <button type="submit" className="button" disabled={submitting || !selected.available}>
          {submitting ? 'Booking…' : `Book for ${formatPrice(selected.price)}`}
        </button>
      </form>
    </section>
  )
}
