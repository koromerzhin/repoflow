import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { PullRequestsPage } from '@/pages/PullRequestsPage'
import { getPullRequests, getRepositories } from '@/services/apiClient'
import type { PullRequestListResponse, RepositoryListResponse } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return { ...actual, getPullRequests: vi.fn(), getRepositories: vi.fn() }
})

const repositories: RepositoryListResponse = {
  items: [
    {
      id: 'repo-1',
      owner: 'acme',
      name: 'web-app',
      full_name: 'acme/web-app',
      default_branch: 'main',
      private: false,
      open_issues_count: 3,
      open_pull_requests_count: 2,
      last_updated: '2026-01-01T10:00:00Z',
      html_url: 'https://github.com/acme/web-app',
      is_demo: true,
    },
  ],
  total: 1,
  data_source: 'demo',
}

const pullRequests: PullRequestListResponse = {
  items: [
    {
      id: 'pr-1',
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
      mergeable: true,
      changed_files: 2,
      additions: 30,
      deletions: 5,
      merge_eligibility: { eligible: true, blockers: [] },
      created_at: '2026-01-01T08:00:00Z',
      updated_at: '2026-01-02T08:00:00Z',
      html_url: 'https://github.com/acme/web-app/pull/142',
      is_demo: true,
    },
    {
      id: 'pr-2',
      number: 143,
      repository_full_name: 'acme/web-app',
      title: 'Mise à jour des dépendances',
      author: 'lea.b',
      state: 'open',
      is_draft: false,
      source_branch: 'chore/deps',
      target_branch: 'main',
      checks_state: 'failure',
      review_decision: 'review_required',
      checks: [],
      mergeable: false,
      changed_files: 1,
      additions: 4,
      deletions: 0,
      merge_eligibility: {
        eligible: false,
        blockers: [
          { code: 'checks_failed', message: 'Checks CI en échec.' },
          { code: 'review_required', message: 'Approbation manquante.' },
        ],
      },
      created_at: '2026-01-01T09:00:00Z',
      updated_at: '2026-01-02T09:00:00Z',
      html_url: 'https://github.com/acme/web-app/pull/143',
      is_demo: true,
    },
  ],
  total: 2,
  data_source: 'demo',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <PullRequestsPage />
    </MemoryRouter>,
  )
}

describe('PullRequestsPage', () => {
  it('affiche les pull requests avec leur état', async () => {
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getPullRequests).mockResolvedValue(pullRequests)

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Refonte du module de facturation')).toBeInTheDocument(),
    )
    expect(screen.getByText('#142')).toBeInTheDocument()
    expect(screen.getByText('acme/web-app · sam.r')).toBeInTheDocument()
    expect(screen.getByText('feature/billing → main')).toBeInTheDocument()
    expect(screen.getAllByText('Ouverte')).toHaveLength(2)
    expect(screen.getByText('Approuvée')).toBeInTheDocument()
    expect(screen.getByText('Réussi')).toBeInTheDocument()
    expect(screen.getByText('Éligible à la fusion')).toBeInTheDocument()
    expect(screen.getByText(/2 fichier\(s\) · \+30 \/ −5/)).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Voir sur GitHub' })[0]).toHaveAttribute(
      'href',
      'https://github.com/acme/web-app/pull/142',
    )
    expect(getPullRequests).toHaveBeenCalled()
  })

  it('détaille les blocages d’une pull request non éligible', async () => {
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getPullRequests).mockResolvedValue(pullRequests)

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Mise à jour des dépendances')).toBeInTheDocument(),
    )
    expect(screen.getByText('2 blocage(s)')).toBeInTheDocument()
    expect(screen.getByText(/Checks CI en échec/)).toBeInTheDocument()
    expect(screen.getByText(/Approbation manquante/)).toBeInTheDocument()
    expect(screen.getByText('Échoué')).toBeInTheDocument()
    expect(screen.getByText('Revue requise')).toBeInTheDocument()
    expect(screen.getByText('Aucun check CI.')).toBeInTheDocument()
  })

  it('filtre les pull requests par dépôt', async () => {
    const user = userEvent.setup()
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getPullRequests).mockResolvedValue(pullRequests)
    vi.mocked(getPullRequests).mockClear()

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Refonte du module de facturation')).toBeInTheDocument(),
    )

    await user.selectOptions(
      screen.getByRole('combobox'),
      await screen.findByRole('option', { name: 'acme/web-app' }),
    )

    await waitFor(() =>
      expect(getPullRequests).toHaveBeenLastCalledWith(
        { repository: 'acme/web-app', refresh: false },
        expect.anything(),
      ),
    )
  })

  it('affiche un état vide', async () => {
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getPullRequests).mockResolvedValue({ items: [], total: 0, data_source: 'demo' })

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Aucune pull request à afficher pour ce filtre.')).toBeInTheDocument(),
    )
  })

  it('affiche une erreur exploitable', async () => {
    const { ApiError } = await import('@/services/apiClient')
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getPullRequests).mockRejectedValue(new ApiError('Panne.', 500, 'internal_error'))

    renderPage()

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Panne.'))
  })
})