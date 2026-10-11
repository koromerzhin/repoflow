import { Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export function PageLoader() {
  const { t } = useTranslation()
  return (
    <div
      role="status"
      className="flex items-center justify-center gap-3 rounded-lg border border-slate-800 bg-slate-900/40 px-6 py-12 text-slate-300"
    >
      <Loader2 className="size-5 animate-spin text-sky-400" aria-hidden />
      <span>{t('common.loading')}</span>
    </div>
  )
}