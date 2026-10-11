import {
  CircleDashed,
  CheckCircle2,
  FolderGit2,
  GitMerge,
  GitPullRequest,
  XCircle,
} from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { AsyncState } from '@/components/AsyncState'
import { AutoRefreshSelect } from '@/components/AutoRefreshSelect'
import { CounterCard } from '@/components/CounterCard'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { useAutoRefresh } from '@/hooks/useAutoRefresh'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { useAsync, useResource } from '@/hooks/useAsync'
import { aggregateSnapshots, seriesFor } from '@/lib/snapshots'
import { formatDateTime } from '@/lib/status'
import { getDashboard, getSnapshots } from '@/services/apiClient'

const TREND_WINDOW_DAYS = 30

function trendSince(days: number): string {
  const date = new Date()
  date.setUTCDate(date.getUTCDate() - (days - 1))
  return date.toISOString().slice(0, 10)
}

export function DashboardPage() {
  const { t } = useTranslation()
  useDocumentTitle(t('dashboard.title'))
  const [autoSeconds, setAutoSeconds] = useState(0)
  const { data, error, loading, reload, refresh } = useResource(
    (options, signal) => getDashboard(signal, { refresh: options.refresh }),
    [],
  )

  const since = useMemo(() => trendSince(TREND_WINDOW_DAYS), [])
  const snapshots = useAsync(
    (signal) => getSnapshots({ since, limit: 500 }, signal),
    [since],
  )
  const trend = useMemo(
    () => aggregateSnapshots(snapshots.data?.items ?? []),
    [snapshots.data],
  )

  const reloadSnapshots = snapshots.reload
  const refreshAll = useCallback(() => {
    refresh()
    reloadSnapshots()
  }, [refresh, reloadSnapshots])

  useAutoRefresh(refreshAll, autoSeconds > 0 ? autoSeconds * 1000 : null)
  const counters = data?.counters
  const trendLabel = (counter: string) =>
    t('dashboard.trendAria', { counter, days: TREND_WINDOW_DAYS })

  return (
    <div>
      <PageHeader
        title={t('dashboard.title')}
        description={t('dashboard.description')}
        actions={
          <div className="flex items-center gap-2">
            <AutoRefreshSelect value={autoSeconds} onChange={setAutoSeconds} />
            <RefreshButton onClick={refreshAll} loading={loading} />
          </div>
        }
      />

      <AsyncState loading={loading} error={error} onRetry={reload}>
        {counters ? (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
            <CounterCard
              label={t('dashboard.counters.repositories')}
              value={counters.repositories}
              icon={FolderGit2}
              accent="text-sky-400"
              trend={seriesFor(trend, 'repositories')}
              trendLabel={trendLabel(t('dashboard.counters.repositories'))}
            />
            <CounterCard
              label={t('dashboard.counters.openPullRequests')}
              value={counters.open_pull_requests}
              icon={GitPullRequest}
              accent="text-indigo-400"
              trend={seriesFor(trend, 'open_pull_requests')}
              trendLabel={trendLabel(t('dashboard.counters.openPullRequests'))}
            />
            <CounterCard
              label={t('dashboard.counters.readyToMerge')}
              value={counters.pull_requests_ready_to_merge}
              icon={GitMerge}
              accent="text-emerald-400"
              hint={t('dashboard.counters.readyToMergeHint')}
              trend={seriesFor(trend, 'pull_requests_ready_to_merge')}
              trendLabel={trendLabel(t('dashboard.counters.readyToMerge'))}
            />
            <CounterCard
              label={t('dashboard.counters.failingChecks')}
              value={counters.pull_requests_with_failing_checks}
              icon={XCircle}
              accent="text-red-400"
              trend={seriesFor(trend, 'pull_requests_with_failing_checks')}
              trendLabel={trendLabel(t('dashboard.counters.failingChecks'))}
            />
            <CounterCard
              label={t('dashboard.counters.pendingChecks')}
              value={counters.pull_requests_pending_checks}
              icon={CircleDashed}
              accent="text-amber-400"
              trend={seriesFor(trend, 'pull_requests_pending_checks')}
              trendLabel={trendLabel(t('dashboard.counters.pendingChecks'))}
            />
            <CounterCard
              label={t('dashboard.counters.openIssues')}
              value={counters.open_issues}
              icon={CheckCircle2}
              accent="text-slate-300"
              trend={seriesFor(trend, 'open_issues')}
              trendLabel={trendLabel(t('dashboard.counters.openIssues'))}
            />
          </div>
        ) : null}

        {data ? (
          <section className="mt-8">
            <h2 className="mb-3 text-lg font-semibold text-slate-100">
              {t('dashboard.recentActivity')}
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
