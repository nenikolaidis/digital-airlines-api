import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { useAuth } from '../authContext'
import type { Registration } from '../types'

const EMPTY: Registration = {
  name: '',
  surname: '',
  email: '',
  password: '',
  date_of_birth: '',
  country_of_origin: '',
  passport_number: '',
}

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function field(name: keyof Registration) {
    return { value: form[name], required: true, onChange: (e: { target: { value: string } }) => setForm({ ...form, [name]: e.target.value }) }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await register(form)
      navigate('/', { replace: true })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="narrow">
      <h1>Create an account</h1>
      <form className="card form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            First name
            <input autoComplete="given-name" {...field('name')} />
          </label>
          <label>
            Last name
            <input autoComplete="family-name" {...field('surname')} />
          </label>
        </div>
        <label>
          Email
          <input type="email" autoComplete="email" {...field('email')} />
        </label>
        <label>
          Password
          <input type="password" autoComplete="new-password" minLength={8} {...field('password')} />
          <span className="hint">At least 8 characters</span>
        </label>
        <div className="form-row">
          <label>
            Date of birth
            <input type="date" autoComplete="bday" {...field('date_of_birth')} />
          </label>
          <label>
            Country
            <input autoComplete="country-name" {...field('country_of_origin')} />
          </label>
        </div>
        <label>
          Passport number
          <input {...field('passport_number')} />
        </label>
        {error && <p className="alert">{error}</p>}
        <button type="submit" className="button" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="muted">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  )
}
