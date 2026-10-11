import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { RepositoriesPage } from '@/pages/RepositoriesPage'
import { getRepositories } from '@/services/apiClient'
import type { RepositoryListResponse } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return { ...actual, getRepositories: vi.fn() }
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
      name: 'billing',
      full_name: 'acme/billing',
      default_branch: 'develop',
      private: true,
      open_issues_count: 0,
      open_pull_requests_count: 0,
      last_updated: '2026-01-02T10:00:00Z',
      html_url: 'https://github.com/acme/billing',
      is_demo: true,
    },
  ],
  total: 2,
  data_source: 'demo',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <RepositoriesPage />
    </MemoryRouter>,
  )
}

describe('RepositoriesPage', () => {
  it('affiche la liste des dépôts suivis', async () => {
    vi.mocked(getRepositories).mockResolvedValue(repositories)

    renderPage()

    await waitFor(() => expect(screen.getByText('acme/web-app')).toBeInTheDocument())
    expect(screen.getByText('acme/billing')).toBeInTheDocument()
    expect(screen.getByText('main')).toBeInTheDocument()
    expect(screen.getByText('develop')).toBeInTheDocument()
    expect(screen.getByText('Public')).toBeInTheDocument()
    expect(screen.getByText('Privé')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Ouvrir' })[0]).toHaveAttribute(
      'href',
      'https://github.com/acme/web-app',
    )
    expect(getRepositories).toHaveBeenCalled()
  })

  it('lie chaque dépôt vers ses pull requests et ses issues', async () => {
    vi.mocked(getRepositories).mockResolvedValue(repositories)

    renderPage()

    await waitFor(() => expect(screen.getByText('acme/web-app')).toBeInTheDocument())

    expect(screen.getByRole('link', { name: 'Voir les 3 issues du dépôt' })).toHaveAttribute(
      'href',
      '/issues?repository=acme%2Fweb-app',
    )
    expect(
      screen.getByRole('link', { name: 'Voir les 1 pull requests du dépôt' }),
    ).toHaveAttribute('href', '/pull-requests?repository=acme%2Fweb-app')
    expect(screen.getByRole('link', { name: 'Voir les 0 issues du dépôt' })).toHaveAttribute(
      'href',
      '/issues?repository=acme%2Fbilling',
    )
  })

  it('affiche un état vide', async () => {
    vi.mocked(getRepositories).mockResolvedValue({ items: [], total: 0, data_source: 'demo' })

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Aucun dépôt suivi pour le moment.')).toBeInTheDocument(),
    )
  })

  it('affiche une erreur exploitable', async () => {
    const { ApiError } = await import('@/services/apiClient')
    vi.mocked(getRepositories).mockRejectedValue(new ApiError('Panne.', 500, 'internal_error'))

    renderPage()

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Panne.'))
  })
})