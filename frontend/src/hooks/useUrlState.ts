import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

export function useUrlState(
  key: string,
  fallback: string,
): [string, (value: string) => void] {
  const [searchParams, setSearchParams] = useSearchParams()
  const value = searchParams.get(key) ?? fallback
  const setValue = useCallback(
    (next: string) => {
      setSearchParams(
        (current) => {
          const params = new URLSearchParams(current)
          if (next && next !== fallback) {
            params.set(key, next)
          } else {
            params.delete(key)
          }
          return params
        },
        { replace: true },
      )
    },
    [fallback, key, setSearchParams],
  )
  return [value, setValue]
}