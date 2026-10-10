import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AsyncState } from '@/components/AsyncState'
import { ApiError } from '@/services/apiClient'

describe('AsyncState', () => {
  it('affiche un état de chargement', () => {
    render(
      <AsyncState loading error={null}>
        <p>contenu</p>
      </AsyncState>,
    )
    expect(screen.getByRole('status')).toHaveTextContent('Chargement')
  })

  it('affiche une erreur et permet de réessayer', () => {
    const error = new ApiError('Service indisponible.', 503, 'unavailable')
    render(
      <AsyncState loading={false} error={error} onRetry={() => undefined}>
        <p>contenu</p>
      </AsyncState>,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Service indisponible.')
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeInTheDocument()
  })

  it('affiche un état vide', () => {
    render(
      <AsyncState loading={false} error={null} isEmpty emptyMessage="Rien à afficher.">
        <p>contenu</p>
      </AsyncState>,
    )
    expect(screen.getByText('Rien à afficher.')).toBeInTheDocument()
  })

  it('affiche le contenu en cas de succès', () => {
    render(
      <AsyncState loading={false} error={null}>
        <p>contenu</p>
      </AsyncState>,
    )
    expect(screen.getByText('contenu')).toBeInTheDocument()
  })
})
