import { useEffect } from 'react'

export function useAutoRefresh(refresh: () => void, intervalMs: number | null) {
  useEffect(() => {
    if (intervalMs === null || intervalMs <= 0) {
      return
    }
    const id = window.setInterval(() => {
      if (document.visibilityState === 'visible') {
        refresh()
      }
    }, intervalMs)
    return () => window.clearInterval(id)
  }, [intervalMs, refresh])
}