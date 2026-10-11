import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { AsyncState } from '@/components/AsyncState'
import { AutoRefreshSelect } from '@/components/AutoRefreshSelect'
import { Badge } from '@/components/Badge'
import { FilterBar } from '@/components/FilterBar'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { RepositoryCombobox } from '@/components/RepositoryCombobox'
import { SearchField } from '@/components/SearchField'
import { VisibilityBadge } from '@/components/VisibilityBadge'
import { useAutoRefresh } from '@/hooks/useAutoRefresh'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { useUrlState } from '@/hooks/useUrlState'
import { CheckStateBadge, PullRequestStateBadge, ReviewDecisionBadge } from '@/components/StateBadges'
import { useAsync, useResource } from '@/hooks/useAsync'
import { getPullRequests, getRepositories } from '@/services/apiClient'

export function PullRequestsPage() {
  const { t } = useTranslation()
  useDocumentTitle(t('pr.title'))
  const [repository, setRepository] = useUrlState('repository', '')
  const [query, setQuery] = useUrlState('q', '')
  const [autoSeconds, setAutoSeconds] = useState(0)

  const repositories = useAsync(getRepositories, [])
  const pullRequests = useResource(
    (options, signal) =>
      getPullRequests(
        {
          repository: repository || undefined,
          search: query || undefined,
          refresh: options.refresh,
        },
        signal,
      ),
    [repository, query],
  )
  useAutoRefresh(pullRequests.refresh, autoSeconds > 0 ? autoSeconds * 1000 : null)

  const items = pullRequests.data?.items ?? []
  const searching = query.trim().length > 0
  const visibility = useMemo(
    () =>
      new Map(
        (repositories.data?.items ?? []).map((item) => [item.full_name, item.private]),
      ),
    [repositories.data],
  )

  const announcement = pullRequests.data
    ? t(repository ? 'pr.announcementFor' : 'pr.announcement', {
        total: pullRequests.data.total,
        repository,
      })
    : ''

  return (
    <div>
      <PageHeader title={t('pr.title')} description={t('pr.description')} />

      <FilterBar>
        <SearchField
          label={t('filter.search')}
          placeholder={t('filter.searchPlaceholder')}
          value={query}
          onChange={setQuery}
        />
        <RepositoryCombobox
          label={t('pr.filterRepository')}
          repositories={repositories.data?.items ?? []}
          value={repository}
          onChange={setRepository}
        />
        <div className="ml-auto flex items-center gap-2">
          <AutoRefreshSelect value={autoSeconds} onChange={setAutoSeconds} />
          <RefreshButton onClick={pullRequests.refresh} loading={pullRequests.loading} />
        </div>
      </FilterBar>

      <p aria-live="polite" className="sr-only">
        {announcement}
      </p>

      <AsyncState
        loading={pullRequests.loading}
        error={pullRequests.error}
        isEmpty={pullRequests.data !== undefined && items.length === 0}
        emptyMessage={searching ? t('pr.noMatch') : t('pr.empty')}
        onRetry={pullRequests.reload}
      >
        <div className="space-y-4">
          {items.map((pr) => (
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
                  <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-400">
                    {pr.repository_full_name}
                    <VisibilityBadge isPrivate={visibility.get(pr.repository_full_name)} /> ·{' '}
                    {pr.author}
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
                  <span className="text-xs text-slate-500">{t('pr.noChecks')}</span>
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
                <span className="text-xs text-slate-500">{t('pr.requiredCheck')}</span>
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4">
                <div className="text-xs text-slate-400">
                  {t('pr.fileCount', { count: pr.changed_files })} · +{pr.additions} / −
                  {pr.deletions}
                </div>
                <div className="flex items-center gap-3">
                  {pr.merge_eligibility.eligible ? (
                    <Badge className="bg-emerald-500/15 text-emerald-300 ring-emerald-500/30">
                      {t('pr.eligible')}
                    </Badge>
                  ) : (
                    <Badge className="bg-slate-500/15 text-slate-300 ring-slate-500/30">
                      {t('pr.blockers', { count: pr.merge_eligibility.blockers.length })}
                    </Badge>
                  )}
                  <a
                    href={pr.html_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-sky-400 hover:text-sky-300"
                  >
                    {t('pr.viewOnGitHub')}
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
        {t('pr.footerPrefix')}{' '}
        <Link to="/repositories" className="text-sky-400 hover:text-sky-300">
          {t('pr.footerRepositories')}
        </Link>
        .
      </p>
    </div>
  )
}
