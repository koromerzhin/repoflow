import { useTranslation } from 'react-i18next'

const options = [
  { value: 0, labelKey: 'filter.autoOff' },
  { value: 30, labelKey: 'filter.auto30s' },
  { value: 60, labelKey: 'filter.auto60s' },
]

interface AutoRefreshSelectProps {
  value: number
  onChange: (value: number) => void
}

export function AutoRefreshSelect({ value, onChange }: AutoRefreshSelectProps) {
  const { t } = useTranslation()
  return (
    <select
      aria-label={t('filter.autoRefresh')}
      value={value}
      onChange={(event) => onChange(Number(event.target.value))}
      className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-200 focus:border-sky-500 focus:outline-none"
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {t(option.labelKey)}
        </option>
      ))}
    </select>
  )
}