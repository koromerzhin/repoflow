import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import { useTranslation } from 'react-i18next'

import i18n from '@/i18n'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'

function LoadingLabel() {
  const { t } = useTranslation()
  return <p>{t('common.loading')}</p>
}

describe('LanguageSwitcher', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('fr')
  })

  it('affiche le français par défaut', () => {
    render(<LanguageSwitcher />)
    const select = screen.getByRole('combobox', { name: 'Langue' })
    expect(select).toHaveValue('fr')
  })

  it('bascule vers l’anglais et traduit les libellés', async () => {
    const user = userEvent.setup()
    render(
      <div>
        <LanguageSwitcher />
        <LoadingLabel />
      </div>,
    )
    const select = screen.getByRole('combobox', { name: 'Langue' })

    await user.selectOptions(select, 'en')

    expect(i18n.language).toBe('en')
    expect(select).toHaveValue('en')
    expect(screen.getByText('Loading…')).toBeInTheDocument()
  })

  it('persiste la langue choisie en localStorage', async () => {
    const user = userEvent.setup()
    render(<LanguageSwitcher />)
    const select = screen.getByRole('combobox', { name: 'Langue' })

    await user.selectOptions(select, 'en')

    expect(window.localStorage.getItem('i18nextLng')).toBe('en')
  })
})