import { createContext, useContext } from 'react'
import type { request } from './api'
import type { Registration, User } from './types'

export interface AuthContextValue {
  user: User | null
  login: (email: string, password: string) => Promise<User>
  register: (registration: Registration) => Promise<User>
  logout: () => Promise<void>
  // Calls the API with the user's token; a rejected token logs the user out
  authRequest: <T>(path: string, options?: Parameters<typeof request>[1]) => Promise<T>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
