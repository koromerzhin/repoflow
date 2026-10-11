import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { AsyncState } from '@/components/AsyncState'
import { AutoRefreshSelect } from '@/components/AutoRefreshSelect'
import { FilterBar } from '@/components/FilterBar'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { RepositoryCombobox } from '@/components/RepositoryCombobox'
import { SearchField } from '@/components/SearchField'
import { VisibilityBadge } from '@/components/VisibilityBadge'
import { IssueStateBadge } from '@/components/StateBadges'
import { useAsync, useResource } from '@/hooks/useAsync'
import { useAutoRefresh } from '@/hooks/useAutoRefresh'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { useUrlState } from '@/hooks/useUrlState'
import { formatDateTime } from '@/lib/status'
import { getIssues, getRepositories } from '@/services/apiClient'
import type { Issue, IssueState } from '@/types/api'

interface Page {
  offset: number
  items: Issue[]
}

type StateFilter = IssueState | 'all'

const stateOptions: { value: StateFilter; labelKey: string }[] = [
  { value: 'open', labelKey: 'issues.state.open' },
  { value: 'closed', labelKey: 'issues.state.closed' },
  { value: 'all', labelKey: 'issues.state.all' },
]

function distinctSorted(values: (string | null)[]): string[] {
  return [...new Set(values.filter((value): value is string => Boolean(value)))].sort(
    (a, b) => a.localeCompare(b),
  )
}

export function IssuesPage() {
  const { t } = useTranslation()
  useDocumentTitle(t('issues.title'))
  const [repository, setRepository] = useUrlState('repository', '')
  const [stateParam, setStateParam] = useUrlState('state', 'open')
  const [query, setQuery] = useUrlState('q', '')
  const [autoSeconds, setAutoSeconds] = useState(0)
  const [labelFilter, setLabelFilter] = useState('')
  const [assigneeFilter, setAssigneeFilter] = useState('')
  const [milestoneFilter, setMilestoneFilter] = useState('')
  const [offset, setOffset] = useState(0)
  const [pages, setPages] = useState<Page[]>([])
  const state: StateFilter = (stateOptions.some((option) => option.value === stateParam)
    ? stateParam
    : 'open') as StateFilter

  const repositories = useAsync(getRepositories, [])
  const issues = useResource(
    (options, signal) =>
      getIssues(
        {
          repository: repository || undefined,
          state,
          search: query || undefined,
          offset,
          refresh: options.refresh,
        },
        signal,
      ),
    [repository, state, query, offset],
  )
  useAutoRefresh(issues.refresh, autoSeconds > 0 ? autoSeconds * 1000 : null)

  const response = issues.data

  useEffect(() => {
    if (!response) {
      return
    }
    /* eslint-disable react-hooks/set-state-in-effect -- accumulation des
       pages : la réponse courante remplace la page à son offset. */
    setPages((current) => {
      const others = current.filter((page) => page.offset !== offset)
      return [...others, { offset, items: response.items }].sort((a, b) => a.offset - b.offset)
    })
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [response, offset])

  const loadedItems = useMemo(() => pages.flatMap((page) => page.items), [pages])
  const nextCursor = response?.next_cursor ?? null

  function changeServerFilter(
    next: { query?: string; repository?: string; state?: string } = {},
  ) {
    const queryValue = next.query ?? query
    const repositoryValue = next.repository ?? repository
    const stateValue = next.state ?? state
    let changed = false
    if (queryValue !== query) {
      setQuery(queryValue)
      changed = true
    }
    if (repositoryValue !== repository) {
      setRepository(repositoryValue)
      changed = true
    }
    if (stateValue !== state) {
      setStateParam(stateValue)
      changed = true
    }
    if (!changed) {
      return
    }
    setPages([])
    setOffset(0)
  }

  const labelOptions = useMemo(() => distinctSorted(loadedItems.flatMap((i) => i.labels)), [
    loadedItems,
  ])
  const assigneeOptions = useMemo(
    () => distinctSorted(loadedItems.flatMap((i) => i.assignees)),
    [loadedItems],
  )
  const milestoneOptions = useMemo(
    () => distinctSorted(loadedItems.map((i) => i.milestone)),
    [loadedItems],
  )

  const filteredItems = useMemo(
    () =>
      loadedItems.filter(
        (issue) =>
          (!labelFilter || issue.labels.includes(labelFilter)) &&
          (!assigneeFilter || issue.assignees.includes(assigneeFilter)) &&
          (!milestoneFilter || issue.milestone === milestoneFilter),
      ),
    [loadedItems, labelFilter, assigneeFilter, milestoneFilter],
  )

  const searching = query.trim().length > 0 || labelFilter || assigneeFilter || milestoneFilter
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
          onChange={(value) => changeServerFilter({ query: value })}
        />
        <RepositoryCombobox
          label={t('issues.filterRepository')}
          repositories={repositories.data?.items ?? []}
          value={repository}
          onChange={(value) => changeServerFilter({ repository: value })}
        />
        <select
          aria-label={t('issues.filterState')}
          value={state}
          onChange={(event) => changeServerFilter({ state: event.target.value })}
          className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
        >
          {stateOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {t(option.labelKey)}
            </option>
          ))}
        </select>
        {labelOptions.length > 0 ? (
          <select
            aria-label={t('issues.filterLabel')}
            value={labelFilter}
            onChange={(event) => setLabelFilter(event.target.value)}
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
          >
            <option value="">{t('issues.anyLabel')}</option>
            {labelOptions.map((label) => (
              <option key={label} value={label}>
                {label}
              </option>
            ))}
          </select>
        ) : null}
        {assigneeOptions.length > 0 ? (
          <select
            aria-label={t('issues.filterAssignee')}
            value={assigneeFilter}
            onChange={(event) => setAssigneeFilter(event.target.value)}
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
          >
            <option value="">{t('issues.anyAssignee')}</option>
            {assigneeOptions.map((assignee) => (
              <option key={assignee} value={assignee}>
                {assignee}
              </option>
            ))}
          </select>
        ) : null}
        {milestoneOptions.length > 0 ? (
          <select
            aria-label={t('issues.filterMilestone')}
            value={milestoneFilter}
            onChange={(event) => setMilestoneFilter(event.target.value)}
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
          >
            <option value="">{t('issues.anyMilestone')}</option>
            {milestoneOptions.map((milestone) => (
              <option key={milestone} value={milestone}>
                {milestone}
              </option>
            ))}
          </select>
        ) : null}
        <div className="ml-auto flex items-center gap-2">
          <AutoRefreshSelect value={autoSeconds} onChange={setAutoSeconds} />
          <RefreshButton onClick={issues.refresh} loading={issues.loading} />
        </div>
      </FilterBar>

      <p aria-live="polite" className="sr-only">
        {announcement}
      </p>

      <AsyncState
        loading={issues.loading && filteredItems.length === 0}
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
                    {issue.assignees.length > 0 ? (
                      <span className="text-slate-500">
                        · {t('issues.assignedTo')} {issue.assignees.map((a) => `@${a}`).join(', ')}
                      </span>
                    ) : null}
                    {issue.milestone ? (
                      <span className="text-slate-500">· {issue.milestone}</span>
                    ) : null}
                  </p>
                  {issue.labels.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {issue.labels.map((label) => (
                        <span
                          key={label}
                          className="rounded-full bg-sky-500/10 px-2 py-0.5 text-[11px] font-medium text-sky-300 ring-1 ring-inset ring-sky-500/20"
                        >
                          {label}
                        </span>
                      ))}
                    </div>
                  ) : null}
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

      {nextCursor !== null ? (
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => setOffset(nextCursor)}
            disabled={issues.loading}
            className="rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-100 transition hover:border-sky-600 hover:text-sky-300 focus:border-sky-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
          >
            {t('common.loadMore')}
          </button>
        </div>
      ) : null}

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