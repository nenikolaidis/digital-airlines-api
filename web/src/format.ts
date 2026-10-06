import { useEffect, useState } from 'react'

export function formatDate(isoDate: string) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function formatPrice(amount: number) {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: Number.isInteger(amount) ? 0 : 2,
  }).format(amount)
}

// True once `active` has stayed true for a few seconds: the free demo server may be waking up
export function useSlowNotice(active: boolean, delayMs = 3000) {
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    if (!active) return
    const timer = setTimeout(() => setSlow(true), delayMs)
    return () => {
      clearTimeout(timer)
      setSlow(false)
    }
  }, [active, delayMs])
  return active && slow
}
