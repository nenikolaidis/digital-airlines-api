import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { useAuth } from '../authContext'
import { useSlowNotice } from '../format'

const DEMO_USER = { email: 'nearchos@example.com', password: 'user1234' }

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  // Pages that need a login send the user here and remember where they came from
  const redirectTo = (useLocation().state as { from?: string } | null)?.from ?? '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const slow = useSlowNotice(submitting)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await login(email, password)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="narrow">
      <h1>Log in</h1>
      <form className="card form" onSubmit={handleSubmit}>
        <label>
          Email
          <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p className="alert">{error}</p>}
        {slow && <p className="muted">The free demo server is waking up, which can take up to a minute.</p>}
        <button type="submit" className="button" disabled={submitting}>
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
        <button
          type="button"
          className="button button-secondary"
          onClick={() => {
            setEmail(DEMO_USER.email)
            setPassword(DEMO_USER.password)
          }}
        >
          Fill in the demo account
        </button>
      </form>
      <p className="muted">
        New here? <Link to="/register">Create an account</Link>
      </p>
    </section>
  )
}
