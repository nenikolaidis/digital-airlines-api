import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router'
import { useAuth } from '../authContext'
import { formatDate, formatPrice, useSlowNotice } from '../format'
import type { PageInfo, Reservation } from '../types'

const PER_PAGE = 10

type Trips = PageInfo & { reservations: Reservation[] }

function todayIso() {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export default function TripsPage() {
  const { authRequest } = useAuth()
  // Set by the booking page after a successful booking
  const booked = (useLocation().state as { booked?: string } | null)?.booked

  const [page, setPage] = useState(1)
  const [trips, setTrips] = useState<Trips | null>(null)
  const [error, setError] = useState('')
  const [cancelling, setCancelling] = useState<string | null>(null)
  const slow = useSlowNotice(!trips && !error)

  const load = useCallback(
    () =>
      authRequest<Trips>(`/reservations?page=${page}&per_page=${PER_PAGE}`)
        .then((data) => {
          setTrips(data)
          setError('')
        })
        .catch((err: Error) => setError(err.message)),
    [authRequest, page],
  )

  useEffect(() => {
    load()
  }, [load])

  async function cancel(reservation: Reservation) {
    const route = `${reservation.flight?.departure_airport} → ${reservation.flight?.destination_airport}`
    if (!window.confirm(`Cancel your ${reservation.ticket_class} ticket for ${route}?`)) return
    setCancelling(reservation.reservation_code)
    try {
      await authRequest(`/reservations/${reservation.reservation_code}`, { method: 'DELETE' })
      // Go back a page if this was the last trip on it
      if (trips && trips.count === 1 && page > 1) setPage(page - 1)
      else await load()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setCancelling(null)
    }
  }

  const today = todayIso()
  return (
    <section>
      <h1>My trips</h1>
      {booked && <p className="notice">Booked! Your reservation code is {booked}.</p>}
      {error && <p className="alert">{error}</p>}
      {!trips && !error && (
        <p className="muted">Loading your trips…{slow && ' The free demo server is waking up, which can take up to a minute.'}</p>
      )}

      {trips && trips.total === 0 && (
        <div className="card empty">
          <p>You haven't booked any flights yet.</p>
          <Link to="/" className="button">
            Find a flight
          </Link>
        </div>
      )}

      {trips && trips.total > 0 && (
        <>
          <div className="list">
            {trips.reservations.map((reservation) => {
              const departed = (reservation.flight?.flight_date ?? today) < today
              return (
                <article key={reservation.reservation_code} className={`card trip${departed ? ' departed' : ''}`}>
                  <div>
                    <h3>
                      {reservation.flight
                        ? `${reservation.flight.departure_airport} → ${reservation.flight.destination_airport}`
                        : `Flight ${reservation.flight_code}`}
                    </h3>
                    <p className="muted">
                      {reservation.flight && `${formatDate(reservation.flight.flight_date)} · `}
                      Flight {reservation.flight_code} · {reservation.ticket_class === 'economy' ? 'Economy' : 'Business'}
                    </p>
                    <p className="muted">
                      {reservation.passenger.first_name} {reservation.passenger.last_name} · Code{' '}
                      <strong className="code">{reservation.reservation_code}</strong>
                    </p>
                  </div>
                  <div className="trip-side">
                    <span className="fare-price">{formatPrice(reservation.price)}</span>
                    {departed ? (
                      <span className="muted">Departed</span>
                    ) : (
                      <button
                        type="button"
                        className="button button-secondary button-small"
                        disabled={cancelling === reservation.reservation_code}
                        onClick={() => cancel(reservation)}
                      >
                        {cancelling === reservation.reservation_code ? 'Cancelling…' : 'Cancel'}
                      </button>
                    )}
                  </div>
                </article>
              )
            })}
          </div>
          {trips.pages > 1 && (
            <nav className="pagination" aria-label="Trip pages">
              <button type="button" className="button button-secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                Previous
              </button>
              <span className="muted">
                Page {trips.page} of {trips.pages}
              </span>
              <button
                type="button"
                className="button button-secondary"
                disabled={page >= trips.pages}
                onClick={() => setPage(page + 1)}
              >
                Next
              </button>
            </nav>
          )}
        </>
      )}
    </section>
  )
}
