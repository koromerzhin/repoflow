import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { DashboardPage } from '@/pages/DashboardPage'
import { getDashboard } from '@/services/apiClient'
import type { DashboardResponse } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return { ...actual, getDashboard: vi.fn() }
})

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
      occurred_at: '2026-01-01T09:00:00Z',
    },
  ],
}

describe('DashboardPage', () => {
  it('affiche les indicateurs du tableau de bord', async () => {
    vi.mocked(getDashboard).mockResolvedValue(dashboard)

    render(<DashboardPage />)

    await waitFor(() => expect(screen.getByText('Dépôts suivis')).toBeInTheDocument())

    expect(screen.getByText('Prêtes à fusionner')).toBeInTheDocument()
    expect(screen.getByText('23')).toBeInTheDocument()
    expect(screen.getByText('PR #142 mise à jour.')).toBeInTheDocument()
  })

  it('affiche une erreur exploitable', async () => {
    const { ApiError } = await import('@/services/apiClient')
    vi.mocked(getDashboard).mockRejectedValue(new ApiError('Panne.', 500, 'internal_error'))

    render(<DashboardPage />)

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Panne.'))
  })
})
