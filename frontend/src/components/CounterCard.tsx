import type { LucideIcon } from 'lucide-react'

interface CounterCardProps {
  label: string
  value: number
  icon: LucideIcon
  accent?: string
  hint?: string
}

export function CounterCard({
  label,
  value,
  icon: Icon,
  accent = 'text-sky-400',
  hint,
}: CounterCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-slate-400">{label}</p>
        <Icon className={`size-5 ${accent}`} aria-hidden />
      </div>
      <p className="mt-3 text-3xl font-semibold tabular-nums text-slate-50">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  )
}
