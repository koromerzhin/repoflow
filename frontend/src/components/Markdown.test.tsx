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

    // Le HTML est interprété puis nettoyé : l'image est rendue, mais le
    // gestionnaire d'événement est éliminé par la liste blanche.
    const img = screen.getByRole('img')
    expect(img).toHaveAttribute('src', 'x')
    expect(img).not.toHaveAttribute('onerror')
    expect(screen.getByText('Texte visible.')).toBeInTheDocument()
  })

  it('élimine complètement les scripts et les URLs dangereuses', () => {
    render(<Markdown>{'<script>alert(1)</script>\n\n[Lien](javascript:alert(1))'}</Markdown>)

    expect(document.querySelector('script')).not.toBeInTheDocument()
    const anchor = screen.getByText('Lien').closest('a')
    expect(anchor?.getAttribute('href') ?? '').not.toContain('javascript')
  })

  it('rend le HTML embarqué type Renovate (details/summary)', () => {
    render(
      <Markdown>
        {'Bumps [release-it](https://github.com/release-it/release-it).\n<details>\n<summary>Release notes</summary>\n<p><em>Sourced from release-it releases.</em></p>\n<h2>Release 21.0.2</h2>\n<ul>\n<li>Prevent duplicate comments</li>\n</ul>\n</details>'}
      </Markdown>,
    )

    expect(screen.getByRole('group')).toBeInTheDocument()
    expect(screen.getByText('Release notes')).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { level: 2, name: 'Release 21.0.2' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Prevent duplicate comments')).toBeInTheDocument()
    expect(screen.getByText(/Sourced from/)).toBeInTheDocument()
  })

  it('rend un corps réel de Renovate sans fuiter de balises visibles', () => {
    // Extrait représentatif de koromerzhin/taskfiles PR #26 (fixe, pour la
    // non-régression) : markdown + <details> + <em>, <code> embarqués.
    const body = [
      'Bumps [release-it](https://github.com/release-it/release-it) from 19.2.4 to 21.0.2.',
      '<details>',
      '<summary>Release notes</summary>',
      '<p><em>Sourced from <a href="https://github.com/release-it/release-it/releases">release-it&#x27;s releases</a>.</em></p>',
      '<blockquote>',
      '<h2>Release 21.0.2</h2>',
      '<ul>',
      '<li>Prevent duplicate comments on resolved issues and PRs (<a href="https://redirect.github.com/release-it/release-it/issues/1324">#1324</a>) - thanks <a href="https://github.com/krisu-pl"><code>@​krisu-pl</code></a>!</li>',
      '</ul>',
      '</blockquote>',
      '</details>',
    ].join('\n')

    render(<Markdown>{body}</Markdown>)

    expect(screen.getByRole('link', { name: 'release-it' })).toHaveAttribute(
      'href',
      'https://github.com/release-it/release-it',
    )
    expect(screen.getByText(/from 19\.2\.4 to 21\.0\.2/)).toBeInTheDocument()
    expect(screen.getByRole('group')).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { level: 2, name: 'Release 21.0.2' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '#1324' })).toHaveAttribute(
      'href',
      'https://redirect.github.com/release-it/release-it/issues/1324',
    )
    // Aucune balise ne fuit sous forme de texte visible.
    expect(screen.queryByText(/<\/?(details|summary|ul|li|blockquote)/)).not.toBeInTheDocument()
  })

  it('ouvre les liens externes sans accès à window.opener', () => {
    render(<Markdown>{'[Documentation](https://example.com/docs)'}</Markdown>)

    const link = screen.getByRole('link', { name: 'Documentation' })
    expect(link).toHaveAttribute('href', 'https://example.com/docs')
    expect(link).toHaveAttribute('rel', 'noreferrer')
  })
})
