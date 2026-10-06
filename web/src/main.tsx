import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { AuthProvider } from './auth'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import './index.css'
import BookPage from './pages/BookPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import RegisterPage from './pages/RegisterPage'
import SearchPage from './pages/SearchPage'
import TripsPage from './pages/TripsPage'

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { index: true, element: <SearchPage /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      {
        path: 'book/:code',
        element: (
          <RequireAuth role="user">
            <BookPage />
          </RequireAuth>
        ),
      },
      {
        path: 'trips',
        element: (
          <RequireAuth role="user">
            <TripsPage />
          </RequireAuth>
        ),
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </StrictMode>,
)
