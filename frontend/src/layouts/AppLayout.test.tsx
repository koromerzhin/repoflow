import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { AppLayout } from '@/layouts/AppLayout'
import { getHealth } from '@/services/apiClient'
import type { HealthResponse } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return { ...actual, getHealth: vi.fn() }
})

function renderLayout() {
  return render(
    <MemoryRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<div>Contenu de la page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

function health(overrides: Partial<HealthResponse> = {}): HealthResponse {
  return {
    status: 'ok',
    app: 'RepoFlow',
    version: '0.1.0',
    environment: 'development',
    timestamp: '2026-01-01T10:00:00Z',
    data_source: 'demo',
    database: 'ok',
    kill_switch_engaged: false,
    ...overrides,
  }
}

describe('AppLayout', () => {
  it('affiche l’état de santé et le mode démonstration', async () => {
    vi.mocked(getHealth).mockResolvedValue(health())

    renderLayout()

    await waitFor(() => expect(screen.getByText('API opérationnelle')).toBeInTheDocument())
    expect(screen.getByRole('note')).toHaveTextContent('Mode démonstration')
    expect(screen.getByText('Contenu de la page')).toBeInTheDocument()
    expect(screen.getByText('Supervision multi-dépôts GitHub')).toBeInTheDocument()
  })

  it('signale une API dégradée et un arrêt d’urgence', async () => {
    vi.mocked(getHealth).mockResolvedValue(
      health({ status: 'degraded', database: 'unavailable', kill_switch_engaged: true, data_source: 'github' }),
    )

    renderLayout()

    await waitFor(() => expect(screen.getByText('API dégradée')).toBeInTheDocument())
    expect(screen.getByText("Arrêt d'urgence actif")).toBeInTheDocument()
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
  })

  it('affiche un avertissement quand le quota GitHub est bas', async () => {
    vi.mocked(getHealth).mockResolvedValue(
      health({
        data_source: 'github',
        github_rate_limit: { remaining: 42, limit: 5000, reset_at: '2026-01-01T11:00:00Z' },
      }),
    )

    renderLayout()

    await waitFor(() =>
      expect(screen.getByText('Quota GitHub : 42 requêtes restantes')).toBeInTheDocument(),
    )
  })

  it('ne signale rien quand le quota GitHub est confortable', async () => {
    vi.mocked(getHealth).mockResolvedValue(
      health({
        data_source: 'github',
        github_rate_limit: { remaining: 4123, limit: 5000, reset_at: '2026-01-01T11:00:00Z' },
      }),
    )

    renderLayout()

    await waitFor(() => expect(screen.getByText('API opérationnelle')).toBeInTheDocument())
    expect(screen.queryByText(/Quota GitHub/)).not.toBeInTheDocument()
  })

  it('ouvre et ferme le menu latéral sur petit écran', async () => {
    const user = userEvent.setup()
    vi.mocked(getHealth).mockResolvedValue(health())

    renderLayout()

    await user.click(screen.getByRole('button', { name: 'Ouvrir le menu' }))
    const closeButtons = screen.getAllByRole('button', { name: 'Fermer le menu' })
    expect(closeButtons).toHaveLength(2)
    await user.click(closeButtons[1])
    expect(screen.queryByRole('button', { name: 'Fermer le menu' })).not.toBeInTheDocument()
  })
})