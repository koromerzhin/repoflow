import { AlertTriangle } from 'lucide-react'
import { Component, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  override state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  override render() {
    if (!this.state.hasError) {
      return this.props.children
    }
    return <ErrorFallback />
  }
}

function ErrorFallback() {
  const { t } = useTranslation()
  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-3 rounded-lg border border-red-900/60 bg-red-950/40 px-6 py-8"
    >
      <div className="flex items-center gap-2 text-red-300">
        <AlertTriangle className="size-5" aria-hidden />
        <span className="font-semibold">{t('error.unexpected')}</span>
      </div>
      <button
        type="button"
        onClick={() => window.location.reload()}
        className="rounded-md border border-red-700/60 bg-red-900/30 px-3 py-1.5 text-sm text-red-100 transition hover:bg-red-900/50"
      >
        {t('error.reload')}
      </button>
    </div>
  )
}