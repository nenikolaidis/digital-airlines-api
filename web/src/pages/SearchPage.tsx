import { useEffect, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router'
import { searchFlights } from '../api'
import FlightCard from '../components/FlightCard'
import { useSlowNotice } from '../format'
import type { Flight, PageInfo } from '../types'

const PER_PAGE = 10

type Results = PageInfo & { flights: Flight[] }

interface Outcome {
  search: string
  results?: Results
  error?: string
}

export default function SearchPage() {
  // The search lives in the URL, so results can be bookmarked and the back button works
  const [params, setParams] = useSearchParams()
  const from = params.get('from') ?? ''
  const to = params.get('to') ?? ''
  const date = params.get('date') ?? ''
  const page = Number(params.get('page') ?? '1') || 1

  const [form, setForm] = useState({ from, to, date })
  const [outcome, setOutcome] = useState<Outcome | null>(null)

  const search = params.toString()
  const loading = outcome?.search !== search
  const results = loading ? null : outcome.results
  const error = loading ? '' : outcome.error
  const slow = useSlowNotice(loading)

  useEffect(() => {
    let cancelled = false
    searchFlights({ from, to, date, page, per_page: PER_PAGE })
      .then((data) => !cancelled && setOutcome({ search, results: data }))
      .catch((err: Error) => !cancelled && setOutcome({ search, error: err.message }))
    return () => {
      cancelled = true
    }
  }, [search, from, to, date, page])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const next = new URLSearchParams()
    for (const [key, value] of Object.entries(form)) if (value.trim()) next.set(key, value.trim())
    setParams(next)
  }

  function goToPage(nextPage: number) {
    const next = new URLSearchParams(params)
    next.set('page', String(nextPage))
    setParams(next)
  }

  return (
    <>
      <section className="hero">
        <h1>Where to next?</h1>
        <p className="muted">Search upcoming flights, compare fares and book a seat.</p>
        <form className="search-form card" onSubmit={handleSubmit}>
          <label>
            From
            <input value={form.from} placeholder="Any airport" onChange={(e) => setForm({ ...form, from: e.target.value })} />
          </label>
          <label>
            To
            <input value={form.to} placeholder="Any airport" onChange={(e) => setForm({ ...form, to: e.target.value })} />
          </label>
          <label>
            Date
            <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
          </label>
          <button type="submit" className="button">
            Search
          </button>
        </form>
      </section>

      <section aria-live="polite">
        {loading && (
          <p className="muted">
            Loading flights…
            {slow && ' The free demo server is waking up, which can take up to a minute.'}
          </p>
        )}
        {error && <p className="alert">{error}</p>}
        {!loading && results && (
          <>
            <p className="muted">
              {results.total === 0 ? 'No flights match your search.' : `${results.total} flight${results.total === 1 ? '' : 's'} found`}
            </p>
            <div className="list">
              {results.flights.map((flight) => (
                <FlightCard key={flight.code} flight={flight} />
              ))}
            </div>
            {results.pages > 1 && (
              <nav className="pagination" aria-label="Result pages">
                <button type="button" className="button button-secondary" disabled={page <= 1} onClick={() => goToPage(page - 1)}>
                  Previous
                </button>
                <span className="muted">
                  Page {results.page} of {results.pages}
                </span>
                <button
                  type="button"
                  className="button button-secondary"
                  disabled={page >= results.pages}
                  onClick={() => goToPage(page + 1)}
                >
                  Next
                </button>
              </nav>
            )}
          </>
        )}
      </section>
    </>
  )
}
