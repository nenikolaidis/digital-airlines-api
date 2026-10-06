import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { useAuth } from '../authContext'
import type { Role } from '../types'

interface Props {
  role?: Role
  children: ReactNode
}

// Sends logged-out visitors to the login page, and back here afterwards
export default function RequireAuth({ role, children }: Props) {
  const { user } = useAuth()
  const location = useLocation()

  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  if (role && user.role !== role) {
    return (
      <section className="narrow">
        <h1>Not available</h1>
        <p className="muted">This page is only for {role} accounts.</p>
      </section>
    )
  }
  return children
}
