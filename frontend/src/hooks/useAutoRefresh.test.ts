import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAutoRefresh } from '@/hooks/useAutoRefresh'

describe('useAutoRefresh', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('ne rafraîchit pas quand désactivé', () => {
    const refresh = vi.fn()
    renderHook(() => useAutoRefresh(refresh, null))
    act(() => {
      vi.advanceTimersByTime(120_000)
    })
    expect(refresh).not.toHaveBeenCalled()
  })

  it('rafraîchit à l’intervalle configuré', () => {
    const refresh = vi.fn()
    renderHook(() => useAutoRefresh(refresh, 30_000))
    act(() => {
      vi.advanceTimersByTime(65_000)
    })
    expect(refresh).toHaveBeenCalledTimes(2)
  })

  it('ignore les intervalles quand l’onglet est masqué', () => {
    const refresh = vi.fn()
    const visibility = Object.getOwnPropertyDescriptor(document, 'visibilityState')
    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      value: 'hidden',
    })
    try {
      renderHook(() => useAutoRefresh(refresh, 30_000))
      act(() => {
        vi.advanceTimersByTime(65_000)
      })
      expect(refresh).not.toHaveBeenCalled()
    } finally {
      if (visibility) {
        Object.defineProperty(document, 'visibilityState', visibility)
      }
    }
  })
})