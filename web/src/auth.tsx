import { useCallback, useMemo, useState, type ReactNode } from 'react'
import * as api from './api'
import { ApiError } from './api'
import { AuthContext } from './authContext'
import type { Registration, User } from './types'

interface Session {
  token: string
  user: User
  expiresAt: number
}


const STORAGE_KEY = 'digital-airlines-session'

function loadSession(): Session | null {
  try {
    const session = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? 'null') as Session | null
    return session && session.expiresAt > Date.now() ? session : null
  } catch {
    return null
  }
}

function saveSession(session: Session | null) {
  try {
    if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Storage can be unavailable (e.g. private mode); the session then lasts until the page reloads
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(loadSession)

  const updateSession = useCallback((next: Session | null) => {
    saveSession(next)
    setSession(next)
  }, [])

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.login(email, password)
      updateSession({
        token: response.access_token,
        user: response.user,
        expiresAt: Date.now() + response.expires_in * 1000,
      })
      return response.user
    },
    [updateSession],
  )

  const register = useCallback(
    async (registration: Registration) => {
      await api.register(registration)
      return login(registration.email, registration.password)
    },
    [login],
  )

  const authRequest = useCallback(
    async <T,>(path: string, options: Parameters<typeof api.request>[1] = {}) => {
      if (!session || session.expiresAt <= Date.now()) {
        updateSession(null)
        throw new ApiError(401, 'Your session has expired. Log in again.')
      }
      try {
        return await api.request<T>(path, { ...options, token: session.token })
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) updateSession(null)
        throw error
      }
    },
    [session, updateSession],
  )

  const logout = useCallback(async () => {
    // Ask the API to invalidate the token too; log out locally even if that fails
    await authRequest('/auth/logout', { method: 'POST' }).catch(() => undefined)
    updateSession(null)
  }, [authRequest, updateSession])

  const value = useMemo(
    () => ({ user: session?.user ?? null, login, register, logout, authRequest }),
    [session, login, register, logout, authRequest],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

