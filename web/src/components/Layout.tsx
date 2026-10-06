import { NavLink, Outlet, useNavigate } from 'react-router'
import { useAuth } from '../authContext'

const API_DOCS_URL = `${import.meta.env.VITE_API_URL ?? 'http://localhost:5000'}/docs`

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <div className="app">
      <header className="header">
        <NavLink to="/" className="brand">
          <span className="brand-mark" aria-hidden="true">
            ✈
          </span>
          Digital Airlines
        </NavLink>
        <nav className="nav">
          <NavLink to="/" end>
            Flights
          </NavLink>
          {user?.role === 'user' && <NavLink to="/trips">My trips</NavLink>}
        </nav>
        <div className="account">
          {user ? (
            <>
              <span className="muted">
                {user.name} {user.role === 'admin' && <span className="badge">admin</span>}
              </span>
              <button type="button" className="link-button" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <NavLink to="/register" className="button button-small">
                Sign up
              </NavLink>
            </>
          )}
        </div>
      </header>

      <main className="main">
        <Outlet />
      </main>

      <footer className="footer muted">
        Demo project: bookings are not real. <a href={API_DOCS_URL}>API documentation</a>
      </footer>
    </div>
  )
}
