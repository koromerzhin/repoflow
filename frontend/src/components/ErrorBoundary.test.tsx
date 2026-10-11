import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ErrorBoundary } from '@/components/ErrorBoundary'

function Boom(): never {
  throw new Error('kaboom')
}

describe('ErrorBoundary', () => {
  it('affiche le contenu quand tout va bien', () => {
    render(
      <ErrorBoundary>
        <p>contenu</p>
      </ErrorBoundary>,
    )
    expect(screen.getByText('contenu')).toBeInTheDocument()
  })

  it('isole un crash de rendu avec un message traduit', () => {
    const consoleError = vi.spyOn(console, 'error')
    consoleError.mockImplementation(() => undefined)

    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    )

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Une erreur inattendue est survenue.',
    )
    expect(
      screen.getByRole('button', { name: 'Recharger la page' }),
    ).toBeInTheDocument()

    consoleError.mockRestore()
  })
})