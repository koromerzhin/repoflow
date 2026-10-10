import { ExternalLink, Lock, Globe } from 'lucide-react'

import { AsyncState } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { useAsync } from '@/hooks/useAsync'
import { formatDateTime } from '@/lib/status'
import { getRepositories } from '@/services/apiClient'

export function RepositoriesPage() {
  const { data, error, loading, reload } = useAsync(getRepositories, [])

  return (
    <div>
      <PageHeader
        title="Dépôts"
        description="Dépôts GitHub suivis par RepoFlow. Aucun clonage local n'est nécessaire."
      />

      <AsyncState
        loading={loading}
        error={error}
        isEmpty={data?.items.length === 0}
        emptyMessage="Aucun dépôt suivi pour le moment."
        onRetry={reload}
      >
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <caption className="sr-only">Liste des dépôts suivis</caption>
            <thead className="bg-slate-900/60 text-left text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th scope="col" className="px-4 py-3 font-medium">
                  Dépôt
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Branche par défaut
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Visibilité
                </th>
                <th scope="col" className="px-4 py-3 text-right font-medium">
                  Issues
                </th>
                <th scope="col" className="px-4 py-3 text-right font-medium">
                  PR
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Dernière activité
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  <span className="sr-only">Lien</span>
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
                        Privé
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5">
                        <Globe className="size-3.5 text-emerald-400" aria-hidden />
                        Public
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
                      Ouvrir
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
