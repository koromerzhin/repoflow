import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ThemeToggle } from '@/components/ThemeToggle'

describe('ThemeToggle', () => {
  afterEach(() => {
    document.documentElement.classList.remove('theme-light')
    window.localStorage.removeItem('repoflow-theme')
    vi.unstubAllGlobals()
  })

  it('reste en thème sombre par défaut', () => {
    render(<ThemeToggle />)
    expect(document.documentElement).not.toHaveClass('theme-light')
    expect(screen.getByRole('button', { name: 'Changer de thème' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
  })

  it('bascule vers le thème clair et persiste le choix', async () => {
    const user = userEvent.setup()
    render(<ThemeToggle />)

    await user.click(screen.getByRole('button', { name: 'Changer de thème' }))

    expect(document.documentElement).toHaveClass('theme-light')
    expect(window.localStorage.getItem('repoflow-theme')).toBe('light')
    expect(screen.getByRole('button', { name: 'Changer de thème' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('restaure le thème clair depuis le localStorage', () => {
    window.localStorage.setItem('repoflow-theme', 'light')
    render(<ThemeToggle />)
    expect(document.documentElement).toHaveClass('theme-light')
  })

  it('suit la préférence système claire en l’absence de choix', () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({ matches: true, addEventListener() {}, removeEventListener() {} }),
    )
    render(<ThemeToggle />)
    expect(document.documentElement).toHaveClass('theme-light')
  })
})