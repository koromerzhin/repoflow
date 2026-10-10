import { RefreshCw } from 'lucide-react'

interface RefreshButtonProps {
  onClick: () => void
  loading?: boolean
}

export function RefreshButton({ onClick, loading = false }: RefreshButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading}
      className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 transition hover:border-sky-600 hover:text-sky-300 disabled:cursor-not-allowed disabled:opacity-50"
    >
      <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} aria-hidden />
      Rafraîchir
    </button>
  )
}