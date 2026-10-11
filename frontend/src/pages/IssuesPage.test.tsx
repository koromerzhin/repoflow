import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { IssuesPage } from '@/pages/IssuesPage'
import { getIssues, getRepositories } from '@/services/apiClient'
import type { IssueListResponse, RepositoryListResponse } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return { ...actual, getIssues: vi.fn(), getRepositories: vi.fn() }
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
      open_pull_requests_count: 1,
      last_updated: '2026-01-01T10:00:00Z',
      html_url: 'https://github.com/acme/web-app',
      is_demo: true,
    },
    {
      id: 'repo-2',
      owner: 'acme',
      name: 'api-gateway',
      full_name: 'acme/api-gateway',
      default_branch: 'main',
      private: true,
      open_issues_count: 2,
      open_pull_requests_count: 0,
      last_updated: '2026-01-01T11:00:00Z',
      html_url: 'https://github.com/acme/api-gateway',
      is_demo: true,
    },
  ],
  total: 2,
  data_source: 'demo',
}

const issues: IssueListResponse = {
  items: [
    {
      id: 'issue-1',
      number: 201,
      repository_full_name: 'acme/web-app',
      title: 'Le lien de réinitialisation expire trop vite',
      author: 'lea.b',
      state: 'open',
      is_pull_request: false,
      labels: ['bug', 'authentification'],
      assignees: ['lea.b'],
      milestone: 'Sprint 12',
      created_at: '2026-01-01T08:00:00Z',
      updated_at: '2026-01-02T08:00:00Z',
      html_url: 'https://github.com/acme/web-app/issues/201',
      is_demo: true,
    },
    {
      id: 'issue-2',
      number: 53,
      repository_full_name: 'acme/api-gateway',
      title: 'Échecs intermittents sur le endpoint /metrics',
      author: 'sami.h',
      state: 'open',
      is_pull_request: false,
      labels: ['bug', 'observabilité'],
      assignees: ['sami.h'],
      milestone: 'Sprint 13',
      created_at: '2026-01-01T09:00:00Z',
      updated_at: '2026-01-02T09:00:00Z',
      html_url: 'https://github.com/acme/api-gateway/issues/53',
      is_demo: true,
    },
  ],
  total: 2,
  data_source: 'demo',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <IssuesPage />
    </MemoryRouter>,
  )
}

describe('IssuesPage', () => {
  it('affiche la liste des issues', async () => {
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getIssues).mockResolvedValue(issues)

    renderPage()

    await waitFor(() =>
      expect(
        screen.getByText('Le lien de réinitialisation expire trop vite'),
      ).toBeInTheDocument(),
    )
    expect(screen.getByText('#201')).toBeInTheDocument()
    expect(screen.getAllByText('Ouverte')).toHaveLength(2)
    expect(getIssues).toHaveBeenCalled()
  })

  it('affiche un état vide quand aucune issue ne correspond', async () => {
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getIssues).mockResolvedValue({ items: [], total: 0, data_source: 'demo' })

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Aucune issue à afficher pour ce filtre.')).toBeInTheDocument(),
    )
  })

  it('filtre les issues par recherche texte côté serveur', async () => {
    const user = userEvent.setup()
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getIssues).mockResolvedValue(issues)

    renderPage()

    await waitFor(() =>
      expect(
        screen.getByText('Le lien de réinitialisation expire trop vite'),
      ).toBeInTheDocument(),
    )

    await user.type(screen.getByRole('searchbox'), 'réinitialisation')

    await waitFor(() => {
      expect(getIssues).toHaveBeenLastCalledWith(
        { state: 'open', search: 'réinitialisation', refresh: false },
        expect.anything(),
      )
    })
  })

  it('filtre les issues par libellé et assigné', async () => {
    const user = userEvent.setup()
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getIssues).mockResolvedValue(issues)

    renderPage()

    await waitFor(() =>
      expect(
        screen.getByText('Le lien de réinitialisation expire trop vite'),
      ).toBeInTheDocument(),
    )
    expect(screen.getAllByText('bug').length).toBeGreaterThan(0)
    expect(screen.getAllByText('authentification').length).toBeGreaterThan(0)
    expect(screen.getByText(/@lea\.b/)).toBeInTheDocument()
    expect(screen.getAllByText(/Sprint 12/).length).toBeGreaterThan(0)

    await user.selectOptions(screen.getByRole('combobox', { name: 'Libellé' }), 'observabilité')
    await waitFor(() => {
      expect(screen.getByText('Échecs intermittents sur le endpoint /metrics')).toBeInTheDocument()
      expect(
        screen.queryByText('Le lien de réinitialisation expire trop vite'),
      ).not.toBeInTheDocument()
    })

    await user.selectOptions(screen.getByRole('combobox', { name: 'Libellé' }), '')
    await user.selectOptions(screen.getByRole('combobox', { name: 'Assigné' }), 'lea.b')
    await waitFor(() => {
      expect(
        screen.getByText('Le lien de réinitialisation expire trop vite'),
      ).toBeInTheDocument()
      expect(
        screen.queryByText('Échecs intermittents sur le endpoint /metrics'),
      ).not.toBeInTheDocument()
    })

    await user.selectOptions(screen.getByRole('combobox', { name: 'Jalon' }), 'Sprint 13')
    await waitFor(() => {
      expect(
        screen.getByText('Aucune issue ne correspond à cette recherche.'),
      ).toBeInTheDocument()
    })
  })

  it('affiche la visibilité du dépôt sur les cartes', async () => {
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getIssues).mockResolvedValue(issues)

    renderPage()

    await waitFor(() =>
      expect(
        screen.getByText('Le lien de réinitialisation expire trop vite'),
      ).toBeInTheDocument(),
    )
    expect(screen.getAllByText('Public').length).toBeGreaterThan(0)
  })

  it('affiche une erreur exploitable', async () => {
    const { ApiError } = await import('@/services/apiClient')
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getIssues).mockRejectedValue(new ApiError('Panne.', 500, 'internal_error'))

    renderPage()

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Panne.'))
  })
})