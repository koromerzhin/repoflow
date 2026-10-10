import { Link } from 'react-router-dom'
import { useState } from 'react'

import { AsyncState } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { IssueStateBadge } from '@/components/StateBadges'
import { useAsync, useResource } from '@/hooks/useAsync'
import { formatDateTime } from '@/lib/status'
import { getIssues, getRepositories } from '@/services/apiClient'
import type { IssueState } from '@/types/api'

type StateFilter = IssueState | 'all'

const stateOptions: { value: StateFilter; label: string }[] = [
  { value: 'open', label: 'Ouvertes' },
  { value: 'closed', label: 'Fermées' },
  { value: 'all', label: 'Toutes' },
]

export function IssuesPage() {
  const [repository, setRepository] = useState('')
  const [state, setState] = useState<StateFilter>('open')

  const repositories = useAsync(getRepositories, [])
  const issues = useResource(
    (options, signal) =>
      getIssues(
        {
          repository: repository || undefined,
          state,
          refresh: options.refresh,
        },
        signal,
      ),
    [repository, state],
  )

  const announcement = issues.data
    ? `${issues.data.total} issue(s) affichée(s)${repository ? ` pour ${repository}` : ''}.`
    : ''

  return (
    <div>
      <PageHeader
        title="Issues"
        description="Issues ouvertes et fermées des dépôts suivis. Les pull requests ne figurent pas dans cette liste."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <RefreshButton onClick={issues.refresh} loading={issues.loading} />
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <span className="hidden sm:inline">Dépôt</span>
              <select
                value={repository}
                onChange={(event) => setRepository(event.target.value)}
                className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
              >
                <option value="">Tous les dépôts</option>
                {repositories.data?.items.map((item) => (
                  <option key={item.id} value={item.full_name}>
                    {item.full_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex items-center gap-2 text-sm text-slate-400">
              <span className="hidden sm:inline">État</span>
              <select
                value={state}
                onChange={(event) => setState(event.target.value as StateFilter)}
                className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
              >
                {stateOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        }
      />

      <p aria-live="polite" className="sr-only">
        {announcement}
      </p>

      <AsyncState
        loading={issues.loading}
        error={issues.error}
        isEmpty={issues.data?.items.length === 0}
        emptyMessage="Aucune issue à afficher pour ce filtre."
        onRetry={issues.reload}
      >
        <ul className="space-y-3">
          {issues.data?.items.map((issue) => (
            <li
              key={issue.id}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-mono text-slate-500">#{issue.number}</span>
                    <h2 className="text-base font-semibold text-slate-100">{issue.title}</h2>
                  </div>
                  <p className="mt-1 text-sm text-slate-400">
                    {issue.repository_full_name} · {issue.author}
                  </p>
                </div>
                <IssueStateBadge state={issue.state} />
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4 text-xs text-slate-400">
                <span>Mise à jour le {formatDateTime(issue.updated_at)}</span>
                <a
                  href={issue.html_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-sky-400 hover:text-sky-300"
                >
                  Voir sur GitHub
                </a>
              </div>
            </li>
          ))}
        </ul>
      </AsyncState>

      <p className="mt-6 text-center text-xs text-slate-600">
        Découvrez aussi les{' '}
        <Link to="/pull-requests" className="text-sky-400 hover:text-sky-300">
          pull requests
        </Link>
        .
      </p>
    </div>
  )
}