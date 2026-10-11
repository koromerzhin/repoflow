import { useSyncExternalStore } from 'react'

import { getToken, getUnauthorized, setToken, subscribe } from '@/lib/auth'

export function useAuth() {
  const token = useSyncExternalStore(subscribe, getToken, getToken)
  const unauthorized = useSyncExternalStore(subscribe, getUnauthorized, getUnauthorized)

  return {
    token,
    unauthorized,
    login: (value: string) => setToken(value),
    logout: () => setToken(null),
  }
}
