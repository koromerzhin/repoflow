import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthGate } from '@/components/AuthGate'
import { getToken, markUnauthorized, resetAuth } from '@/lib/auth'

describe('AuthGate', () => {
  afterEach(() => {
    resetAuth()
    vi.restoreAllMocks()
  })

  it('affiche les enfants quand l’accès est autorisé', () => {
    render(
      <AuthGate>
        <div>Contenu protégé</div>
      </AuthGate>,
    )
    expect(screen.getByText('Contenu protégé')).toBeInTheDocument()
  })

  it('affiche le formulaire après un 401', async () => {
    markUnauthorized()
    render(
      <AuthGate>
        <div>Contenu protégé</div>
      </AuthGate>,
    )

    expect(
      screen.getByRole('heading', { name: 'Authentification requise' }),
    ).toBeInTheDocument()
    expect(screen.queryByText('Contenu protégé')).not.toBeInTheDocument()
  })

  it('ignore une soumission vide', async () => {
    markUnauthorized()
    const user = userEvent.setup()
    render(
      <AuthGate>
        <div>Contenu protégé</div>
      </AuthGate>,
    )

    await user.click(screen.getByRole('button', { name: 'Se connecter' }))
    expect(getToken()).toBeNull()
    expect(
      screen.getByRole('heading', { name: 'Authentification requise' }),
    ).toBeInTheDocument()
  })

  it('enregistre le jeton et lève le verrou', async () => {
    markUnauthorized()
    const user = userEvent.setup()
    render(
      <AuthGate>
        <div>Contenu protégé</div>
      </AuthGate>,
    )

    await user.type(screen.getByLabelText("Jeton d'accès"), 'mon-jeton')
    await user.click(screen.getByRole('button', { name: 'Se connecter' }))

    await waitFor(() => expect(screen.getByText('Contenu protégé')).toBeInTheDocument())
    expect(getToken()).toBe('mon-jeton')
  })
})
