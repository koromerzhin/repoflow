import { Globe, Lock } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface VisibilityBadgeProps {
  isPrivate?: boolean
}

export function VisibilityBadge({ isPrivate }: VisibilityBadgeProps) {
  const { t } = useTranslation()
  if (isPrivate === undefined) {
    return null
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] ring-1 ring-inset bg-slate-500/10 text-slate-300 ring-slate-500/20">
      {isPrivate ? (
        <Lock className="size-3 text-amber-400" aria-hidden />
      ) : (
        <Globe className="size-3 text-emerald-400" aria-hidden />
      )}
      {isPrivate ? t('repositories.private') : t('repositories.public')}
    </span>
  )
}