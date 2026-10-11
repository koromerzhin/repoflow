import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  getToken,
  getUnauthorized,
  markUnauthorized,
  resetAuth,
  setToken,
  subscribe,
} from '@/lib/auth'

describe('auth', () => {
  afterEach(() => {
    resetAuth()
    window.sessionStorage.clear()
  })

  it('mémorise le jeton en session', () => {
    setToken('abc')
    expect(getToken()).toBe('abc')
    expect(window.sessionStorage.getItem('repoflow-api-token')).toBe('abc')
  })

  it('ignore un jeton vide ou espaces', () => {
    setToken('   ')
    expect(getToken()).toBeNull()
  })

  it('déconnecte et nettoie le stockage', () => {
    setToken('abc')
    setToken(null)
    expect(getToken()).toBeNull()
    expect(window.sessionStorage.getItem('repoflow-api-token')).toBeNull()
  })

  it('marque puis réinitialise l’état non autorisé', () => {
    markUnauthorized()
    expect(getUnauthorized()).toBe(true)
    setToken('abc')
    expect(getUnauthorized()).toBe(false)
  })

  it('notifie les abonnés', () => {
    const listener = vi.fn()
    const unsubscribe = subscribe(listener)
    setToken('abc')
    expect(listener).toHaveBeenCalled()
    unsubscribe()
    setToken(null)
    expect(listener).toHaveBeenCalledTimes(1)
  })

  it('relit le jeton depuis le stockage au chargement', async () => {
    window.sessionStorage.setItem('repoflow-api-token', 'stored')
    vi.resetModules()
    const fresh = await import('@/lib/auth')
    expect(fresh.getToken()).toBe('stored')
  })
})
