import {
  CircleDashed,
  CheckCircle2,
  FolderGit2,
  GitMerge,
  GitPullRequest,
  XCircle,
} from 'lucide-react'

import { AsyncState } from '@/components/AsyncState'
import { CounterCard } from '@/components/CounterCard'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { useResource } from '@/hooks/useAsync'
import { formatDateTime } from '@/lib/status'
import { getDashboard } from '@/services/apiClient'

export function DashboardPage() {
  const { data, error, loading, reload, refresh } = useResource(
    (options, signal) => getDashboard(signal, { refresh: options.refresh }),
    [],
  )
  const counters = data?.counters

  return (
    <div>
      <PageHeader
        title="Tableau de bord"
        description="Vue synthétique des dépôts suivis, des pull requests et de l'état des checks CI."
        actions={<RefreshButton onClick={refresh} loading={loading} />}
      />

      <AsyncState loading={loading} error={error} onRetry={reload}>
        {counters ? (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
            <CounterCard
              label="Dépôts suivis"
              value={counters.repositories}
              icon={FolderGit2}
              accent="text-sky-400"
            />
            <CounterCard
              label="PR ouvertes"
              value={counters.open_pull_requests}
              icon={GitPullRequest}
              accent="text-indigo-400"
            />
            <CounterCard
              label="Prêtes à fusionner"
              value={counters.pull_requests_ready_to_merge}
              icon={GitMerge}
              accent="text-emerald-400"
              hint="Évaluation indicative"
            />
            <CounterCard
              label="Checks échoués"
              value={counters.pull_requests_with_failing_checks}
              icon={XCircle}
              accent="text-red-400"
            />
            <CounterCard
              label="Checks en cours"
              value={counters.pull_requests_pending_checks}
              icon={CircleDashed}
              accent="text-amber-400"
            />
            <CounterCard
              label="Issues ouvertes"
              value={counters.open_issues}
              icon={CheckCircle2}
              accent="text-slate-300"
            />
          </div>
        ) : null}

        {data ? (
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-semibold text-slate-100">
              Activité récente
            </h2>
            <ul className="divide-y divide-slate-800 overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
              {data.recent_activity.map((item) => (
                <li
                  key={item.id}
                  className="flex flex-col gap-1 px-5 py-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="text-sm text-slate-200">{item.message}</p>
                    <p className="text-xs text-slate-500">
                      {item.repository_full_name ?? '—'}
                    </p>
                  </div>
                  <time className="text-xs text-slate-500" dateTime={item.occurred_at}>
                    {formatDateTime(item.occurred_at)}
                  </time>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </AsyncState>
    </div>
  )
}
