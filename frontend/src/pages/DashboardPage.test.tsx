import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DashboardPage } from '@/pages/DashboardPage'
import { getDashboard, getHealth, getSnapshots } from '@/services/apiClient'
import type { DashboardResponse, HealthResponse, SnapshotListResponse } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return { ...actual, getDashboard: vi.fn(), getSnapshots: vi.fn(), getHealth: vi.fn() }
})

const healthDemo: HealthResponse = {
  status: 'ok',
  app: 'RepoFlow',
  version: '0.1.0',
  environment: 'test',
  timestamp: '2026-01-01T10:00:00Z',
  data_source: 'demo',
  database: 'ok',
  kill_switch_engaged: false,
  github_rate_limit: null,
}

const dashboard: DashboardResponse = {
  generated_at: '2026-01-01T10:00:00Z',
  data_source: 'demo',
  provider: { name: 'demo', is_demo: true, requires_token: false },
  counters: {
    repositories: 3,
    open_pull_requests: 5,
    pull_requests_ready_to_merge: 1,
    pull_requests_with_failing_checks: 2,
    pull_requests_pending_checks: 1,
    open_issues: 23,
  },
  recent_activity: [
    {
      id: 'a1',
      event_type: 'pull_request_update',
      message: 'PR #142 mise à jour.',
      repository_full_name: 'acme/web-app',
      pull_request_number: 142,
      occurred_at: '2026-01-01T09:00:00Z',
    },
    {
      id: 'a2',
      event_type: 'pull_request_update',
      message: 'PR sans numéro.',
      repository_full_name: null,
      pull_request_number: null,
      occurred_at: '2026-01-01T08:00:00Z',
    },
  ],
}

const emptySnapshots: SnapshotListResponse = { items: [], total: 0, data_source: 'demo' }

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.mocked(getSnapshots).mockResolvedValue(emptySnapshots)
    vi.mocked(getHealth).mockResolvedValue(healthDemo)
  })

  it('affiche le quota GitHub quand le fournisseur en expose un', async () => {
    vi.mocked(getDashboard).mockResolvedValue(dashboard)
    vi.mocked(getHealth).mockResolvedValue({
      ...healthDemo,
      data_source: 'github',
      github_rate_limit: {
        resource: 'core',
        remaining: 4123,
        limit: 5000,
        reset_at: '2026-10-12T14:02:00Z',
      },
    })

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('Dépôts suivis')).toBeInTheDocument())

    const badge = screen.getByTestId('github-quota')
    expect(badge).toHaveTextContent('Quota GitHub')
    expect(badge).toHaveTextContent('4123 / 5000 requêtes')
    expect(badge).toHaveTextContent(/réinitialisation/)
  })

  it('affiche une alerte rouge quand le quota est presque épuisé', async () => {
    vi.mocked(getDashboard).mockResolvedValue(dashboard)
    vi.mocked(getHealth).mockResolvedValue({
      ...healthDemo,
      data_source: 'github',
      github_rate_limit: { resource: 'graphql', remaining: 12, limit: 5000, reset_at: null },
    })

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() =>
      expect(screen.getByTestId('github-quota')).toHaveTextContent('12 / 5000 requêtes'),
    )
    expect(screen.getByTestId('github-quota')).toHaveClass('bg-red-500/15')
  })

  it('n’affiche pas de badge de quota en mode démonstration', async () => {
    vi.mocked(getDashboard).mockResolvedValue(dashboard)

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('Dépôts suivis')).toBeInTheDocument())
    expect(screen.queryByTestId('github-quota')).not.toBeInTheDocument()
  })

  it('affiche les indicateurs du tableau de bord', async () => {
    vi.mocked(getDashboard).mockResolvedValue(dashboard)

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('Dépôts suivis')).toBeInTheDocument())

    expect(screen.getByText('Prêtes à fusionner')).toBeInTheDocument()
    expect(screen.getByText('23')).toBeInTheDocument()
    expect(screen.getByText('PR #142 mise à jour.')).toBeInTheDocument()
  })

  it('lie chaque activité vers la pull request correspondante', async () => {
    vi.mocked(getDashboard).mockResolvedValue(dashboard)

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('PR #142 mise à jour.')).toBeInTheDocument())

    const link = screen.getByRole('link', { name: 'PR #142 mise à jour.' })
    expect(link).toHaveAttribute('href', '/pull-requests/142?repository=acme%2Fweb-app')
    // Une activité sans dépôt lié reste du texte simple.
    expect(screen.getByText('PR sans numéro.').tagName).not.toBe('A')
  })

  it('affiche une erreur exploitable', async () => {
    const { ApiError } = await import('@/services/apiClient')
    vi.mocked(getDashboard).mockRejectedValue(new ApiError('Panne.', 500, 'internal_error'))

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Panne.'))
  })

  it('affiche une tendance par compteur quand un historique existe', async () => {
    vi.mocked(getDashboard).mockResolvedValue(dashboard)
    vi.mocked(getSnapshots).mockResolvedValue({
      items: [
        {
          id: 1,
          repository_full_name: 'acme/web-app',
          snapshot_date: '2026-01-01',
          data_source: 'demo',
          open_pull_requests: 2,
          pull_requests_ready_to_merge: 0,
          pull_requests_with_failing_checks: 1,
          pull_requests_pending_checks: 0,
          open_issues: 20,
        },
        {
          id: 2,
          repository_full_name: 'acme/web-app',
          snapshot_date: '2026-01-02',
          data_source: 'demo',
          open_pull_requests: 5,
          pull_requests_ready_to_merge: 1,
          pull_requests_with_failing_checks: 2,
          pull_requests_pending_checks: 1,
          open_issues: 23,
        },
      ],
      total: 2,
      data_source: 'demo',
    })

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('Dépôts suivis')).toBeInTheDocument())

    // Une sparkline par compteur (six cartes) dès qu'il y a au moins deux jours.
    await waitFor(() => expect(screen.getAllByTestId('sparkline')).toHaveLength(6))
    expect(getSnapshots).toHaveBeenCalled()
  })

  it('masque les tendances sans historique suffisant', async () => {
    vi.mocked(getDashboard).mockResolvedValue(dashboard)

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('Dépôts suivis')).toBeInTheDocument())
    expect(screen.queryAllByTestId('sparkline')).toHaveLength(0)
  })
})
