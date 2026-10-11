import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Markdown } from '@/components/Markdown'

describe('Markdown', () => {
  it('rend les titres, listes et blocs de code', () => {
    render(
      <Markdown>{'## Titre\n\n- élément A\n- élément B\n\n```\ncurl health\n```'}</Markdown>,
    )

    expect(screen.getByRole('heading', { level: 2, name: 'Titre' })).toBeInTheDocument()
    expect(screen.getByText('élément A')).toBeInTheDocument()
    expect(screen.getByText('élément B')).toBeInTheDocument()
    expect(screen.getByText('curl health')).toBeInTheDocument()
  })

  it('rend le Markdown GitHub : cases à cocher, tableaux, barré', () => {
    render(
      <Markdown>
        {'- [x] fait\n\n| Col |\n| --- |\n| 1 |\n\n~~obsolète~~'}
      </Markdown>,
    )

    expect(screen.getByRole('checkbox')).toBeDisabled()
    expect(screen.getByText('obsolète')).toBeInTheDocument()
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('n’interprète jamais le HTML brut (sécurité XSS)', () => {
    render(<Markdown>{'<img src=x onerror="alert(1)" />\n\nTexte visible.'}</Markdown>)

    // Le HTML brut est neutralisé : aucun élément img/script n'est créé,
    // le contenu n'apparaît qu'en texte inerte (échappé).
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(screen.queryByTitle('alert(1)')).not.toBeInTheDocument()
    expect(screen.getByText('Texte visible.')).toBeInTheDocument()
  })

  it('ouvre les liens externes sans accès à window.opener', () => {
    render(<Markdown>{'[Documentation](https://example.com/docs)'}</Markdown>)

    const link = screen.getByRole('link', { name: 'Documentation' })
    expect(link).toHaveAttribute('href', 'https://example.com/docs')
    expect(link).toHaveAttribute('rel', 'noreferrer')
  })
})
