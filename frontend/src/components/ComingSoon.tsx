import { Construction } from 'lucide-react'

import { PageHeader } from '@/components/PageHeader'

interface ComingSoonProps {
  title: string
  description: string
}

export function ComingSoon({ title, description }: ComingSoonProps) {
  return (
    <div>
      <PageHeader title={title} description={description} />
      <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-slate-800 bg-slate-900/30 px-6 py-20 text-center">
        <div className="flex size-14 items-center justify-center rounded-full bg-slate-800/70">
          <Construction className="size-7 text-amber-400" aria-hidden />
        </div>
        <div>
          <p className="text-lg font-semibold text-slate-100">À venir</p>
          <p className="mt-1 max-w-lg text-sm text-slate-400">
            Cette fonctionnalité n'est pas encore disponible. Elle utilise
            volontairement un état explicite plutôt qu'une simulation.
          </p>
        </div>
      </div>
    </div>
  )
}
