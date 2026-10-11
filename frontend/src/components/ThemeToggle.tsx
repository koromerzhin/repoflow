import { Moon, Sun } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { useTheme } from '@/hooks/useTheme'

export function ThemeToggle() {
  const { t } = useTranslation()
  const { theme, toggle } = useTheme()
  return (
    <button
      type="button"
      aria-label={t('app.toggleTheme')}
      aria-pressed={theme === 'light'}
      onClick={toggle}
      className="rounded-md border border-slate-700 bg-slate-900 p-1.5 text-slate-300 transition hover:border-sky-600 hover:text-sky-300"
    >
      {theme === 'dark' ? (
        <Sun className="size-4" aria-hidden />
      ) : (
        <Moon className="size-4" aria-hidden />
      )}
    </button>
  )
}