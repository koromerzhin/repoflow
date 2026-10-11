import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { App } from '@/App'

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('offline')),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('affiche la navigation principale en français', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    const nav = screen.getByRole('navigation', { name: 'Navigation principale' })
    expect(nav).toBeInTheDocument()
    for (const label of [
      'Tableau de bord',
      'Dépôts',
      'Pull requests',
      'Automatisations',
      'Historique',
    ]) {
      expect(screen.getAllByRole('link', { name: label }).length).toBeGreaterThan(0)
    }
  })

  it('affiche la page des automatisations', async () => {
    render(
      <MemoryRouter initialEntries={['/automations']}>
        <App />
      </MemoryRouter>,
    )

    expect(
      await screen.findByRole('heading', { name: 'Automatisations' }),
    ).toBeInTheDocument()
    expect(await screen.findByText('Garde-fous')).toBeInTheDocument()
  })

  it('affiche une page 404 pour une route inconnue', async () => {
    render(
      <MemoryRouter initialEntries={['/inconnue']}>
        <App />
      </MemoryRouter>,
    )
    expect(await screen.findByText('Page introuvable')).toBeInTheDocument()
  })
})
