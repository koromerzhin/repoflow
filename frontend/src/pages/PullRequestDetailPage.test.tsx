import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { PullRequestDetailPage } from '@/pages/PullRequestDetailPage'
import { getPullRequestDetail } from '@/services/apiClient'
import type { PullRequestDetail } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return { ...actual, getPullRequestDetail: vi.fn() }
})

const detail: PullRequestDetail = {
  id: 'pr-142',
  number: 142,
  repository_full_name: 'acme/web-app',
  title: 'Refonte du module de facturation',
  author: 'sam.r',
  state: 'open',
  is_draft: false,
  source_branch: 'feature/billing',
  target_branch: 'main',
  checks_state: 'success',
  review_decision: 'approved',
  checks: [
    {
      name: 'ci/tests',
      state: 'success',
      conclusion: 'success',
      details_url: 'https://github.com/acme/web-app/runs/1',
      required: true,
    },
  ],
  changed_files: 2,
  additions: 30,
  deletions: 5,
  mergeable: true,
  html_url: 'https://github.com/acme/web-app/pull/142',
  created_at: '2026-01-01T08:00:00Z',
  updated_at: '2026-01-02T08:00:00Z',
  merge_eligibility: { eligible: true, blockers: [] },
  is_demo: true,
  body: 'Description de la PR.',
  files: [
    {
      filename: 'src/billing.ts',
      status: 'modified',
      additions: 20,
      deletions: 5,
      changes: 25,
    },
  ],
  reviews: [
    {
      id: 'review-1',
      author: 'lea.b',
      state: 'approved',
      body: 'RAS.',
      submitted_at: '2026-01-02T09:00:00Z',
    },
  ],
  timeline: [
    {
      id: 'event-1',
      event_type: 'opened',
      actor: 'sam.r',
      message: 'a ouvert la pull request',
      created_at: '2026-01-01T08:00:00Z',
    },
  ],
}

function renderPage(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/pull-requests/:number" element={<PullRequestDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('PullRequestDetailPage', () => {
  it('affiche le détail complet d’une pull request', async () => {
    vi.mocked(getPullRequestDetail).mockResolvedValue(detail)

    renderPage('/pull-requests/142?repository=acme/web-app')

    await waitFor(() =>
      expect(screen.getByText('Refonte du module de facturation')).toBeInTheDocument(),
    )
    expect(screen.getByText('src/billing.ts')).toBeInTheDocument()
    expect(screen.getByText('lea.b')).toBeInTheDocument()
    expect(screen.getByText('Description de la PR.')).toBeInTheDocument()
    expect(getPullRequestDetail).toHaveBeenCalledWith(142, 'acme/web-app', expect.anything(), {
      refresh: false,
    })
  })

  it('propose d’ouvrir la PR sur GitHub dans un nouvel onglet', async () => {
    vi.mocked(getPullRequestDetail).mockResolvedValue(detail)

    renderPage('/pull-requests/142?repository=acme/web-app')

    await waitFor(() =>
      expect(screen.getByText('Refonte du module de facturation')).toBeInTheDocument(),
    )

    const link = screen.getByRole('link', { name: 'Voir sur GitHub' })
    expect(link).toHaveAttribute('href', 'https://github.com/acme/web-app/pull/142')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noreferrer')
  })

  it('affiche le corps de la PR et des revues en Markdown', async () => {
    vi.mocked(getPullRequestDetail).mockResolvedValue({
      ...detail,
      body: '## Contexte\n\nCorrige [la facturation](https://example.com/spec).',
      reviews: [
        {
          id: 'review-1',
          author: 'lea.b',
          state: 'approved',
          body: '- [x] Revu en détail',
          submitted_at: '2026-01-02T09:00:00Z',
        },
      ],
    })

    renderPage('/pull-requests/142?repository=acme/web-app')

    await waitFor(() =>
      expect(
        screen.getByRole('heading', { level: 2, name: 'Contexte' }),
      ).toBeInTheDocument(),
    )
    expect(screen.getByRole('link', { name: 'la facturation' })).toHaveAttribute(
      'href',
      'https://example.com/spec',
    )
    expect(screen.getByRole('checkbox')).toBeInTheDocument()
  })

  it('affiche une erreur exploitable', async () => {
    const { ApiError } = await import('@/services/apiClient')
    vi.mocked(getPullRequestDetail).mockRejectedValue(
      new ApiError('Introuvable.', 404, 'pull_request_not_found'),
    )

    renderPage('/pull-requests/999?repository=acme/web-app')

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Introuvable.'))
  })

  it('invite à revenir à la liste sans dépôt', async () => {
    renderPage('/pull-requests/142')

    expect(screen.getByText(/liste des pull requests/i)).toBeInTheDocument()
  })
})