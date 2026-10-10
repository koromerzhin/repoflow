import { useTranslation } from 'react-i18next'

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation()
  const current = i18n.resolvedLanguage?.startsWith('en') ? 'en' : 'fr'

  return (
    <select
      aria-label={t('lang.label')}
      value={current}
      onChange={(event) => {
        void i18n.changeLanguage(event.target.value)
      }}
      className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-200 transition hover:border-sky-600 focus:outline-none focus:ring-1 focus:ring-sky-500"
    >
      <option value="fr">FR</option>
      <option value="en">EN</option>
    </select>
  )
}