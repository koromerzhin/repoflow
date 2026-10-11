import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Drawer } from '@/components/Drawer'

describe('Drawer', () => {
  it('n’affiche rien quand fermé', () => {
    render(
      <Drawer open={false} onClose={() => undefined} label="Menu">
        <p>contenu</p>
      </Drawer>,
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('affiche le panneau et déplace le focus à l’ouverture', () => {
    render(
      <Drawer open onClose={() => undefined} label="Menu">
        <button type="button">Action</button>
      </Drawer>,
    )
    expect(screen.getByRole('dialog', { name: 'Menu' })).toBeInTheDocument()
    expect(
      within(screen.getByRole('dialog', { name: 'Menu' })).getByRole('button', {
        name: 'Fermer le menu',
      }),
    ).toHaveFocus()
    expect(document.body.style.overflow).toBe('hidden')
  })

  it('ferme avec Échap et restaure le scroll', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(
      <Drawer open onClose={onClose} label="Menu">
        <p>contenu</p>
      </Drawer>,
    )

    await user.keyboard('{Escape}')

    expect(onClose).toHaveBeenCalledOnce()
  })

  it('reste focus dans le panneau lors d’un Tab sur le dernier élément', async () => {
    const user = userEvent.setup()
    render(
      <Drawer open onClose={() => undefined} label="Menu">
        <button type="button">Premier</button>
        <button type="button">Dernier</button>
      </Drawer>,
    )
    screen.getByRole('button', { name: 'Dernier' }).focus()

    await user.keyboard('{Tab}')

    const dialog = screen.getByRole('dialog', { name: 'Menu' })
    expect(within(dialog).getByRole('button', { name: 'Fermer le menu' })).toHaveFocus()
  })
})