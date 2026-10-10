import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AutomationsPage } from '@/pages/AutomationsPage'
import {
  createRepositoryConfig,
  getAutomationStatus,
  listRepositoryConfigs,
  setKillSwitch,
  updateRule,
} from '@/services/apiClient'
import type { AutomationStatus, RepositoryConfigListResponse } from '@/types/api'

vi.mock('@/services/apiClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/apiClient')>()
  return {
    ...actual,
    listRepositoryConfigs: vi.fn(),
    getAutomationStatus: vi.fn(),
    createRepositoryConfig: vi.fn(),
    createRule: vi.fn(),
    updateRepositoryConfig: vi.fn(),
    deleteRepositoryConfig: vi.fn(),
    updateRule: vi.fn(),
    deleteRule: vi.fn(),
    setKillSwitch: vi.fn(),
  }
})

const configs: RepositoryConfigListResponse = {
  items: [
    {
      id: 1,
      full_name: 'acme/web-app',
      owner: 'acme',
      name: 'web-app',
      default_branch: 'main',
      enabled: true,
      created_at: '2026-01-01T10:00:00Z',
      updated_at: '2026-01-01T10:00:00Z',
      rules: [
        {
          id: 3,
          repository_id: 1,
          name: 'Fusion vers main',
          branch_pattern: 'main',
          auto_merge_enabled: false,
          required_approvals: 2,
          require_green_checks: true,
          created_at: '2026-01-01T10:00:00Z',
          updated_at: '2026-01-01T10:00:00Z',
        },
      ],
    },
  ],
  total: 1,
}

const status: AutomationStatus = {
  kill_switch_engaged: false,
  global_auto_merge_enabled: false,
  worker_enabled: false,
  worker_interval_seconds: 300,
}

function renderPage() {
  return render(
    <MemoryRouter>
      <AutomationsPage />
    </MemoryRouter>,
  )
}

describe('AutomationsPage', () => {
  beforeEach(() => {
    vi.mocked(listRepositoryConfigs).mockResolvedValue(configs)
    vi.mocked(getAutomationStatus).mockResolvedValue(status)
  })

  it('affiche les dépôts suivis et leurs règles', async () => {
    renderPage()

    await waitFor(() => expect(screen.getByText('acme/web-app')).toBeInTheDocument())
    expect(screen.getByText('Fusion vers main')).toBeInTheDocument()
    expect(screen.getByText('Fusion manuelle')).toBeInTheDocument()
  })

  it('affiche un état vide sans dépôt suivi', async () => {
    vi.mocked(listRepositoryConfigs).mockResolvedValue({ items: [], total: 0 })
    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Aucun dépôt suivi pour le moment.')).toBeInTheDocument(),
    )
  })

  it('engage l’arrêt d’urgence', async () => {
    vi.mocked(setKillSwitch).mockResolvedValue({ ...status, kill_switch_engaged: true })
    renderPage()

    await screen.findByText('acme/web-app')
    fireEvent.click(screen.getByRole('button', { name: /engager/i }))

    await waitFor(() => expect(setKillSwitch).toHaveBeenCalledWith(true))
  })

  it('ajoute un dépôt suivi', async () => {
    vi.mocked(createRepositoryConfig).mockResolvedValue({
      id: 2,
      full_name: 'acme/api',
      owner: 'acme',
      name: 'api',
      default_branch: 'main',
      enabled: true,
      rules: [],
      created_at: '2026-01-01T10:00:00Z',
      updated_at: '2026-01-01T10:00:00Z',
    })
    renderPage()

    await screen.findByText('acme/web-app')
    fireEvent.change(screen.getByLabelText('Dépôt (owner/name)'), {
      target: { value: 'acme/api' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter' }))

    await waitFor(() =>
      expect(createRepositoryConfig).toHaveBeenCalledWith({
        full_name: 'acme/api',
        default_branch: 'main',
      }),
    )
  })

  it('active la fusion automatique d’une règle', async () => {
    vi.mocked(updateRule).mockResolvedValue(configs.items[0].rules[0])
    renderPage()

    await screen.findByText('Fusion vers main')
    fireEvent.click(screen.getByRole('button', { name: 'Activer' }))

    await waitFor(() =>
      expect(updateRule).toHaveBeenCalledWith(3, { auto_merge_enabled: true }),
    )
  })

  it('affiche une erreur exploitable', async () => {
    const { ApiError } = await import('@/services/apiClient')
    vi.mocked(listRepositoryConfigs).mockRejectedValue(new ApiError('Panne.', 500, 'internal_error'))
    renderPage()

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Panne.'))
  })
})
