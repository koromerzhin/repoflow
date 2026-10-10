import { render, screen, waitFor } from '@testing-library/react'
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
  ],
  total: 1,
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
      created_at: '2026-01-01T08:00:00Z',
      updated_at: '2026-01-02T08:00:00Z',
      html_url: 'https://github.com/acme/web-app/issues/201',
      is_demo: true,
    },
  ],
  total: 1,
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
    expect(screen.getByText('Ouverte')).toBeInTheDocument()
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

  it('affiche une erreur exploitable', async () => {
    const { ApiError } = await import('@/services/apiClient')
    vi.mocked(getRepositories).mockResolvedValue(repositories)
    vi.mocked(getIssues).mockRejectedValue(new ApiError('Panne.', 500, 'internal_error'))

    renderPage()

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Panne.'))
  })
})