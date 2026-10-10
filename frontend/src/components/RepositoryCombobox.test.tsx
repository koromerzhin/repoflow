import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { RepositoryCombobox } from '@/components/RepositoryCombobox'
import type { Repository } from '@/types/api'

const repositories: Repository[] = [
  {
    id: 'r1',
    owner: 'acme',
    name: 'web-app',
    full_name: 'acme/web-app',
    default_branch: 'main',
    private: false,
    open_issues_count: 0,
    open_pull_requests_count: 0,
    last_updated: '2026-01-01T10:00:00Z',
    html_url: 'https://github.com/acme/web-app',
    is_demo: true,
  },
  {
    id: 'r2',
    owner: 'acme',
    name: 'private-api',
    full_name: 'acme/private-api',
    default_branch: 'main',
    private: true,
    open_issues_count: 0,
    open_pull_requests_count: 0,
    last_updated: '2026-01-01T11:00:00Z',
    html_url: 'https://github.com/acme/private-api',
    is_demo: true,
  },
]

function renderCombobox(onChange: (value: string) => void = () => undefined, value = '') {
  render(<RepositoryCombobox repositories={repositories} value={value} onChange={onChange} />)
  return screen.getByRole('combobox')
}

describe('RepositoryCombobox', () => {
  it('affiche tous les dépôts avec leur visibilité', async () => {
    const user = userEvent.setup()
    const input = renderCombobox()

    await user.click(input)

    expect(screen.getByRole('option', { name: 'Tous les dépôts' })).toBeInTheDocument()
    expect(
      screen.getByRole('option', { name: /acme\/web-app.*Public/ }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('option', { name: /acme\/private-api.*Privé/ }),
    ).toBeInTheDocument()
  })

  it('filtre les options par saisie', async () => {
    const user = userEvent.setup()
    const input = renderCombobox()

    await user.click(input)
    await user.type(input, 'private')

    await waitFor(() => {
      expect(screen.getByRole('option', { name: /acme\/private-api/ })).toBeInTheDocument()
      expect(screen.queryByRole('option', { name: /acme\/web-app/ })).not.toBeInTheDocument()
    })
  })

  it('sélectionne avec les flèches et Entrée', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const input = renderCombobox(onChange)

    await user.click(input)
    await user.keyboard('{ArrowDown}')
    await user.keyboard('{Enter}')

    expect(onChange).toHaveBeenCalledWith('acme/web-app')
  })

  it('ferme la liste avec Échap sans changer la sélection', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const input = renderCombobox(onChange)

    await user.click(input)
    await user.keyboard('{Escape}')

    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    expect(onChange).not.toHaveBeenCalled()
  })

  it('affiche un message quand aucune option ne correspond', async () => {
    const user = userEvent.setup()
    const input = renderCombobox()

    await user.click(input)
    await user.type(input, 'inexistant')

    await waitFor(() => {
      expect(screen.getByText('Aucun dépôt correspondant.')).toBeInTheDocument()
    })
  })

  it('affiche la valeur sélectionnée et permet de la effacer', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    renderCombobox(onChange, 'acme/web-app')

    const input = screen.getByRole('combobox')
    expect(input).toHaveValue('acme/web-app')

    await user.click(screen.getByRole('button', { name: 'Effacer le dépôt sélectionné' }))

    expect(onChange).toHaveBeenCalledWith('')
  })
})