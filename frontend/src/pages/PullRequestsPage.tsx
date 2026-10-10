import { Link } from 'react-router-dom'
import { useState } from 'react'

import { AsyncState } from '@/components/AsyncState'
import { Badge } from '@/components/Badge'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { CheckStateBadge, PullRequestStateBadge, ReviewDecisionBadge } from '@/components/StateBadges'
import { useAsync, useResource } from '@/hooks/useAsync'
import { getPullRequests, getRepositories } from '@/services/apiClient'

export function PullRequestsPage() {
  const [repository, setRepository] = useState('')

  const repositories = useAsync(getRepositories, [])
  const pullRequests = useResource(
    (options, signal) =>
      getPullRequests(
        { repository: repository || undefined, refresh: options.refresh },
        signal,
      ),
    [repository],
  )

  const announcement = pullRequests.data
    ? `${pullRequests.data.total} pull request(s) affichée(s)${
        repository ? ` pour ${repository}` : ''
      }.`
    : ''

  return (
    <div>
      <PageHeader
        title="Pull requests"
        description="Pull requests ouvertes, état des checks CI et évaluation indicative des conditions de fusion."
        actions={
          <div className="flex items-center gap-3">
            <RefreshButton onClick={pullRequests.refresh} loading={pullRequests.loading} />
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
          </div>
        }
      />

      <p aria-live="polite" className="sr-only">
        {announcement}
      </p>

      <AsyncState
        loading={pullRequests.loading}
        error={pullRequests.error}
        isEmpty={pullRequests.data?.items.length === 0}
        emptyMessage="Aucune pull request à afficher pour ce filtre."
        onRetry={pullRequests.reload}
      >
        <div className="space-y-4">
          {pullRequests.data?.items.map((pr) => (
            <article
              key={pr.id}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-mono text-slate-500">#{pr.number}</span>
                    <h2 className="text-base font-semibold text-slate-100">
                      <Link
                        to={`/pull-requests/${pr.number}?repository=${encodeURIComponent(
                          pr.repository_full_name,
                        )}`}
                        className="hover:text-sky-300"
                      >
                        {pr.title}
                      </Link>
                    </h2>
                  </div>
                  <p className="mt-1 text-sm text-slate-400">
                    {pr.repository_full_name} · {pr.author}
                  </p>
                  <p className="mt-1 font-mono text-xs text-slate-500">
                    {pr.source_branch} → {pr.target_branch}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <PullRequestStateBadge state={pr.state} />
                  <ReviewDecisionBadge decision={pr.review_decision} />
                  <CheckStateBadge state={pr.checks_state} />
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                {pr.checks.length === 0 ? (
                  <span className="text-xs text-slate-500">Aucun check CI.</span>
                ) : (
                  pr.checks.map((check) => (
                    <Badge
                      key={check.name}
                      className={
                        check.state === 'success'
                          ? 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/20'
                          : check.state === 'failure'
                            ? 'bg-red-500/10 text-red-300 ring-red-500/20'
                            : check.state === 'pending'
                              ? 'bg-amber-500/10 text-amber-300 ring-amber-500/20'
                              : 'bg-slate-500/10 text-slate-300 ring-slate-500/20'
                      }
                    >
                      {check.name}
                      {check.required ? <span className="text-slate-500">*</span> : null}
                    </Badge>
                  ))
                )}
                <span className="text-xs text-slate-500">(* check obligatoire)</span>
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4">
                <div className="text-xs text-slate-400">
                  {pr.changed_files} fichier(s) · +{pr.additions} / −{pr.deletions}
                </div>
                <div className="flex items-center gap-3">
                  {pr.merge_eligibility.eligible ? (
                    <Badge className="bg-emerald-500/15 text-emerald-300 ring-emerald-500/30">
                      Éligible à la fusion
                    </Badge>
                  ) : (
                    <Badge className="bg-slate-500/15 text-slate-300 ring-slate-500/30">
                      {pr.merge_eligibility.blockers.length} blocage(s)
                    </Badge>
                  )}
                  <a
                    href={pr.html_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-sky-400 hover:text-sky-300"
                  >
                    Voir sur GitHub
                  </a>
                </div>
              </div>

              {!pr.merge_eligibility.eligible ? (
                <ul className="mt-3 space-y-1 border-t border-slate-800 pt-3 text-xs text-slate-500">
                  {pr.merge_eligibility.blockers.map((blocker) => (
                    <li key={blocker.code}>• {blocker.message}</li>
                  ))}
                </ul>
              ) : null}
            </article>
          ))}
        </div>
      </AsyncState>

      <p className="mt-6 text-center text-xs text-slate-600">
        Découvrez aussi la liste des{' '}
        <Link to="/repositories" className="text-sky-400 hover:text-sky-300">
          dépôts suivis
        </Link>
        .
      </p>
    </div>
  )
}
