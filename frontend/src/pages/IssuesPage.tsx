import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { AsyncState } from '@/components/AsyncState'
import { FilterBar } from '@/components/FilterBar'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { RepositoryCombobox } from '@/components/RepositoryCombobox'
import { SearchField } from '@/components/SearchField'
import { VisibilityBadge } from '@/components/VisibilityBadge'
import { IssueStateBadge } from '@/components/StateBadges'
import { useAsync, useResource } from '@/hooks/useAsync'
import { formatDateTime } from '@/lib/status'
import { matchesQuery } from '@/lib/search'
import { getIssues, getRepositories } from '@/services/apiClient'
import type { IssueState } from '@/types/api'

type StateFilter = IssueState | 'all'

const stateOptions: { value: StateFilter; labelKey: string }[] = [
  { value: 'open', labelKey: 'issues.state.open' },
  { value: 'closed', labelKey: 'issues.state.closed' },
  { value: 'all', labelKey: 'issues.state.all' },
]

export function IssuesPage() {
  const { t } = useTranslation()
  const [repository, setRepository] = useState('')
  const [state, setState] = useState<StateFilter>('open')
  const [query, setQuery] = useState('')

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

  const filteredItems = useMemo(() => {
    const items = issues.data?.items ?? []
    if (!query.trim()) {
      return items
    }
    return items.filter((issue) =>
      matchesQuery(
        `${issue.title} ${issue.author} ${issue.number} ${issue.repository_full_name}`,
        query,
      ),
    )
  }, [issues.data, query])

  const searching = query.trim().length > 0
  const visibility = useMemo(
    () =>
      new Map(
        (repositories.data?.items ?? []).map((item) => [item.full_name, item.private]),
      ),
    [repositories.data],
  )

  const announcement = issues.data
    ? t(repository ? 'issues.announcementFor' : 'issues.announcement', {
        total: searching ? filteredItems.length : issues.data.total,
        repository,
      })
    : ''

  return (
    <div>
      <PageHeader title={t('issues.title')} description={t('issues.description')} />

      <FilterBar>
        <SearchField
          label={t('filter.search')}
          placeholder={t('filter.searchPlaceholder')}
          value={query}
          onChange={setQuery}
        />
        <RepositoryCombobox
          label={t('issues.filterRepository')}
          repositories={repositories.data?.items ?? []}
          value={repository}
          onChange={setRepository}
        />
        <select
          aria-label={t('issues.filterState')}
          value={state}
          onChange={(event) => setState(event.target.value as StateFilter)}
          className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
        >
          {stateOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {t(option.labelKey)}
            </option>
          ))}
        </select>
        <div className="ml-auto">
          <RefreshButton onClick={issues.refresh} loading={issues.loading} />
        </div>
      </FilterBar>

      <p aria-live="polite" className="sr-only">
        {announcement}
      </p>

      <AsyncState
        loading={issues.loading}
        error={issues.error}
        isEmpty={issues.data !== undefined && filteredItems.length === 0}
        emptyMessage={searching ? t('issues.noMatch') : t('issues.empty')}
        onRetry={issues.reload}
      >
        <ul className="space-y-3">
          {filteredItems.map((issue) => (
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
                  <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-400">
                    {issue.repository_full_name}
                    <VisibilityBadge isPrivate={visibility.get(issue.repository_full_name)} /> ·{' '}
                    {issue.author}
                  </p>
                </div>
                <IssueStateBadge state={issue.state} />
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4 text-xs text-slate-400">
                <span>{t('issues.updatedOn', { date: formatDateTime(issue.updated_at) })}</span>
                <a
                  href={issue.html_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-sky-400 hover:text-sky-300"
                >
                  {t('issues.viewOnGitHub')}
                </a>
              </div>
            </li>
          ))}
        </ul>
      </AsyncState>

      <p className="mt-6 text-center text-xs text-slate-600">
        {t('issues.footerPrefix')}{' '}
        <Link to="/pull-requests" className="text-sky-400 hover:text-sky-300">
          {t('issues.footerPullRequests')}
        </Link>
        .
      </p>
    </div>
  )
}