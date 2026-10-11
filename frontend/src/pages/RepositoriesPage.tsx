import { ExternalLink, Lock, Globe } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { AsyncState } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { useResource } from '@/hooks/useAsync'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { formatDateTime } from '@/lib/status'
import { getRepositories } from '@/services/apiClient'

export function RepositoriesPage() {
  const { t } = useTranslation()
  useDocumentTitle(t('repositories.title'))
  const { data, error, loading, reload, refresh } = useResource(
    (options, signal) => getRepositories(signal, { refresh: options.refresh }),
    [],
  )

  return (
    <div>
      <PageHeader
        title={t('repositories.title')}
        description={t('repositories.description')}
        actions={<RefreshButton onClick={refresh} loading={loading} />}
      />

      <AsyncState
        loading={loading}
        error={error}
        isEmpty={data?.items.length === 0}
        emptyMessage={t('repositories.empty')}
        onRetry={reload}
      >
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <caption className="sr-only">{t('repositories.caption')}</caption>
            <thead className="bg-slate-900/60 text-left text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th scope="col" className="px-4 py-3 font-medium">
                  {t('repositories.col.repository')}
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  {t('repositories.col.defaultBranch')}
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  {t('repositories.col.visibility')}
                </th>
                <th scope="col" className="px-4 py-3 text-right font-medium">
                  {t('repositories.col.issues')}
                </th>
                <th scope="col" className="px-4 py-3 text-right font-medium">
                  {t('repositories.col.pullRequests')}
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  {t('repositories.col.lastActivity')}
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  <span className="sr-only">{t('repositories.col.link')}</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {data?.items.map((repository) => (
                <tr key={repository.id} className="hover:bg-slate-900/40">
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-100">{repository.full_name}</div>
                    <div className="text-xs text-slate-500">{repository.owner}</div>
                  </td>
                  <td className="px-4 py-3">
                    <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-300">
                      {repository.default_branch}
                    </code>
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {repository.private ? (
                      <span className="inline-flex items-center gap-1.5">
                        <Lock className="size-3.5 text-amber-400" aria-hidden />
                        {t('repositories.private')}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5">
                        <Globe className="size-3.5 text-emerald-400" aria-hidden />
                        {t('repositories.public')}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-300">
                    {repository.open_issues_count}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-300">
                    {repository.open_pull_requests_count}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {formatDateTime(repository.last_updated)}
                  </td>
                  <td className="px-4 py-3">
                    <a
                      href={repository.html_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-sky-400 hover:text-sky-300"
                    >
                      {t('repositories.open')}
                      <ExternalLink className="size-3.5" aria-hidden />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </AsyncState>
    </div>
  )
}
