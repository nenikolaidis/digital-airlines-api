import type { Flight, LoginResponse, PageInfo, Registration, User } from './types'

// In development Vite forwards /api to the Flask server; in production this is the API's URL
const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  token?: string | null
}

export async function request<T>(path: string, { method = 'GET', body, token }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(BASE_URL + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.")
  }

  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, data?.error ?? `Request failed with status ${response.status}.`)
  }
  return data as T
}

export interface FlightSearch {
  from?: string
  to?: string
  date?: string
  page?: number
  per_page?: number
}

export function searchFlights(search: FlightSearch) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(search)) {
    if (value !== undefined && value !== '') params.set(key, String(value))
  }
  return request<PageInfo & { flights: Flight[] }>(`/flights?${params}`)
}

export function getFlight(code: string) {
  return request<{ flight: Flight }>(`/flights/${encodeURIComponent(code)}`)
}

export function login(email: string, password: string) {
  return request<LoginResponse>('/auth/login', { method: 'POST', body: { email, password } })
}

export function register(registration: Registration) {
  return request<{ message: string; user: User }>('/auth/register', { method: 'POST', body: registration })
}
