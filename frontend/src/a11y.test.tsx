import { render, screen } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'

import { AuthGate } from '@/components/AuthGate'
import { ThemeToggle } from '@/components/ThemeToggle'
import { markUnauthorized, resetAuth } from '@/lib/auth'
import { expectNoA11yViolations } from '@/test/a11y'

describe('accessibilité (axe)', () => {
  afterEach(() => {
    resetAuth()
    document.documentElement.classList.remove('theme-light')
  })

  it('écran de connexion sans violation', async () => {
    markUnauthorized()
    render(
      <AuthGate>
        <div>Contenu</div>
      </AuthGate>,
    )
    await screen.findByRole('heading', { name: 'Authentification requise' })
    await expectNoA11yViolations()
  })

  it('sélecteur de thème sans violation', async () => {
    render(<ThemeToggle />)
    await expectNoA11yViolations()
  })
})
