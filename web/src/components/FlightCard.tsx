import type { ReactNode } from 'react'
import { formatDate, formatPrice } from '../format'
import type { Flight, TicketClass } from '../types'

const CLASS_LABELS: Record<TicketClass, string> = { economy: 'Economy', business: 'Business' }

interface Props {
  flight: Flight
  // Rendered next to each ticket class, e.g. a "Book" button
  renderAction?: (ticketClass: TicketClass) => ReactNode
}

export default function FlightCard({ flight, renderAction }: Props) {
  return (
    <article className="card flight-card">
      <div className="flight-route">
        <div>
          <h3>
            {flight.departure_airport} <span className="arrow">→</span> {flight.destination_airport}
          </h3>
          <p className="muted">
            {formatDate(flight.flight_date)} · Flight {flight.code}
          </p>
        </div>
      </div>
      <ul className="fares">
        {(Object.keys(CLASS_LABELS) as TicketClass[]).map((ticketClass) => {
          const { available, price } = flight.tickets[ticketClass]
          return (
            <li key={ticketClass} className="fare">
              <span className="fare-class">{CLASS_LABELS[ticketClass]}</span>
              <span className="fare-price">{formatPrice(price)}</span>
              <span className={available ? 'muted' : 'sold-out'}>{available ? `${available} seats left` : 'Sold out'}</span>
              {renderAction?.(ticketClass)}
            </li>
          )
        })}
      </ul>
    </article>
  )
}
