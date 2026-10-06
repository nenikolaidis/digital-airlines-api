import { Link } from 'react-router'

export default function NotFoundPage() {
  return (
    <section className="narrow">
      <h1>Page not found</h1>
      <p className="muted">
        This page doesn't exist. <Link to="/">Search flights</Link> instead.
      </p>
    </section>
  )
}
