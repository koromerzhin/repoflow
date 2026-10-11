import { AlertTriangle, Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

import { apiErrorMessage, type ApiError } from '@/services/apiClient'

interface AsyncStateProps {
  loading: boolean
  error: ApiError | null
  isEmpty?: boolean
  emptyMessage?: string
  onRetry?: () => void
  children: ReactNode
}

export function AsyncState({
  loading,
  error,
  isEmpty = false,
  emptyMessage,
  onRetry,
  children,
}: AsyncStateProps) {
  const { t } = useTranslation()

  if (loading) {
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

  if (error) {
    return (
      <div
        role="alert"
        className="flex flex-col items-start gap-3 rounded-lg border border-red-900/60 bg-red-950/40 px-6 py-8"
      >
        <div className="flex items-center gap-2 text-red-300">
          <AlertTriangle className="size-5" aria-hidden />
          <span className="font-semibold">{t('async.errorTitle')}</span>
        </div>
        <p className="text-sm text-red-200/90">{apiErrorMessage(error, t)}</p>
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="rounded-md border border-red-700/60 bg-red-900/30 px-3 py-1.5 text-sm text-red-100 transition hover:bg-red-900/50"
          >
            {t('common.retry')}
          </button>
        ) : null}
      </div>
    )
  }

  if (isEmpty) {
    return (
      <div className="rounded-lg border border-dashed border-slate-800 bg-slate-900/30 px-6 py-12 text-center text-slate-400">
        {emptyMessage ?? t('async.empty')}
      </div>
    )
  }

  return <>{children}</>
}
