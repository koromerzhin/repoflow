import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { HistoryPage } from '@/pages/HistoryPage'
import { getAudit } from '@/services/apiClient'
import type { AuditListResponse } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return { ...actual, getAudit: vi.fn() }
})

const audit: AuditListResponse = {
  items: [
    {
      id: 2,
      event_type: 'merge_succeeded',
      repository_full_name: 'acme/web-app',
      pull_request_number: 142,
      actor: 'system',
      message: 'PR #142 fusionnée (squash).',
      payload: { sha: 'demo-merge-142' },
      occurred_at: '2026-01-02T10:00:00Z',
    },
    {
      id: 1,
      event_type: 'merge_blocked',
      repository_full_name: 'acme/web-app',
      pull_request_number: 138,
      actor: 'system',
      message: 'PR #138 non éligible (2 blocage(s)).',
      payload: { blockers: ['not_approved', 'check_not_success'] },
      occurred_at: '2026-01-02T09:00:00Z',
    },
  ],
  total: 2,
}

function renderPage() {
  return render(
    <MemoryRouter>
      <HistoryPage />
    </MemoryRouter>,
  )
}

describe('HistoryPage', () => {
  beforeEach(() => {
    vi.mocked(getAudit).mockResolvedValue(audit)
  })

  it('affiche les événements du journal', async () => {
    renderPage()

    await waitFor(() => expect(screen.getByText('PR #142 fusionnée (squash).')).toBeInTheDocument())
    expect(screen.getAllByText('Fusion réussie').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Fusion bloquée').length).toBeGreaterThan(0)
    expect(screen.getByText('acme/web-app#142')).toBeInTheDocument()
  })

  it('filtre le journal par type d’événement', async () => {
    renderPage()

    await screen.findByText('PR #142 fusionnée (squash).')
    fireEvent.change(screen.getByLabelText('Type'), {
      target: { value: 'merge_succeeded' },
    })

    await waitFor(() =>
      expect(getAudit).toHaveBeenCalledWith(
        expect.objectContaining({ event_type: 'merge_succeeded' }),
        expect.anything(),
      ),
    )
  })

  it('affiche un journal vide', async () => {
    vi.mocked(getAudit).mockResolvedValue({ items: [], total: 0 })
    renderPage()

    await waitFor(() =>
      expect(
        screen.getByText('Aucun événement dans le journal pour ce filtre.'),
      ).toBeInTheDocument(),
    )
  })

  it('affiche une erreur exploitable', async () => {
    const { ApiError } = await import('@/services/apiClient')
    vi.mocked(getAudit).mockRejectedValue(new ApiError('Panne.', 500, 'internal_error'))
    renderPage()

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Panne.'))
  })
})
