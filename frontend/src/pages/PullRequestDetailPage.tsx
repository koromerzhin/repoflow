import { Link, useParams, useSearchParams } from 'react-router-dom'
import { ExternalLink } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { AsyncState } from '@/components/AsyncState'
import { Badge } from '@/components/Badge'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import {
  CheckStateBadge,
  PullRequestStateBadge,
  ReviewDecisionBadge,
  ReviewStateBadge,
} from '@/components/StateBadges'
import { useResource } from '@/hooks/useAsync'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { fileStatusClasses, fileStatusLabels, formatDateTime } from '@/lib/status'
import { getPullRequestDetail } from '@/services/apiClient'

export function PullRequestDetailPage() {
  const { t } = useTranslation()
  useDocumentTitle(t('detail.title'))
  const { number: numberParam } = useParams<{ number: string }>()
  const [searchParams] = useSearchParams()
  const repository = searchParams.get('repository') ?? ''
  const number = Number(numberParam)

  const detail = useResource(
    (options, signal) =>
      getPullRequestDetail(number, repository, signal, { refresh: options.refresh }),
    [number, repository],
  )

  if (!repository || Number.isNaN(number)) {
    return (
      <div>
        <PageHeader title={t('detail.title')} />
        <div className="rounded-lg border border-dashed border-slate-800 bg-slate-900/30 px-6 py-12 text-center text-slate-400">
          {t('detail.invalidHintPrefix')}{' '}
          <Link to="/pull-requests" className="text-sky-400 hover:text-sky-300">
            {t('detail.invalidHintLink')}
          </Link>
          .
        </div>
      </div>
    )
  }

  const pr = detail.data

  return (
    <div>
      <Link
        to="/pull-requests"
        className="mb-4 inline-block text-sm text-sky-400 hover:text-sky-300"
      >
        {t('detail.back')}
      </Link>

      <PageHeader
        title={pr ? `${pr.title}` : `Pull request #${number}`}
        description={repository}
        actions={
          <div className="flex items-center gap-2">
            {pr ? (
              <a
                href={pr.html_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 transition hover:border-sky-600 hover:text-sky-300 focus:border-sky-500 focus:outline-none"
              >
                {t('detail.viewOnGitHub')}
                <ExternalLink className="size-3.5" aria-hidden />
              </a>
            ) : null}
            <RefreshButton onClick={detail.refresh} loading={detail.loading} />
          </div>
        }
      />

      <AsyncState
        loading={detail.loading}
        error={detail.error}
        onRetry={detail.reload}
      >
        {pr ? (
          <div className="space-y-6">
            <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-mono text-slate-500">#{pr.number}</span>
                <PullRequestStateBadge state={pr.state} />
                <ReviewDecisionBadge decision={pr.review_decision} />
                <CheckStateBadge state={pr.checks_state} />
              </div>
              <p className="mt-2 text-sm text-slate-400">
                {pr.author} · {pr.source_branch} → {pr.target_branch}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {t('pr.fileCount', { count: pr.changed_files })} · +{pr.additions} / −
                {pr.deletions}
              </p>

              {pr.body ? (
                <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/40 p-4">
                  <Markdown>{pr.body}</Markdown>
                </div>
              ) : null}

              <div className="mt-4 border-t border-slate-800 pt-4">
                {pr.merge_eligibility.eligible ? (
                  <Badge className="bg-emerald-500/15 text-emerald-300 ring-emerald-500/30">
                    {t('detail.eligible')}
                  </Badge>
                ) : (
                  <div>
                    <Badge className="bg-slate-500/15 text-slate-300 ring-slate-500/30">
                      {t('detail.blockers', { count: pr.merge_eligibility.blockers.length })}
                    </Badge>
                    <ul className="mt-2 space-y-1 text-xs text-slate-500">
                      {pr.merge_eligibility.blockers.map((blocker) => (
                        <li key={blocker.code}>• {blocker.message}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-lg font-semibold text-slate-100">
                {t('detail.checksTitle')}
              </h2>
              {pr.checks.length === 0 ? (
                <p className="text-sm text-slate-500">{t('detail.noChecks')}</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {pr.checks.map((check) => (
                    <CheckStateBadge key={check.name} state={check.state} />
                  ))}
                </div>
              )}
            </section>

            <section>
              <h2 className="mb-3 text-lg font-semibold text-slate-100">
                {t('detail.filesTitle')} ({pr.files.length})
              </h2>
              {pr.files.length === 0 ? (
                <p className="text-sm text-slate-500">{t('detail.noFiles')}</p>
              ) : (
                <ul className="divide-y divide-slate-800 rounded-xl border border-slate-800 bg-slate-900/40">
                  {pr.files.map((file) => (
                    <li
                      key={file.filename}
                      className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5"
                    >
                      <span className="font-mono text-sm text-slate-300">{file.filename}</span>
                      <span className="flex items-center gap-3 text-xs">
                        <span className={fileStatusClasses[file.status] ?? 'text-slate-400'}>
                          {t(fileStatusLabels[file.status] ?? file.status)}
                        </span>
                        <span className="text-emerald-300">+{file.additions}</span>
                        <span className="text-red-300">−{file.deletions}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section>
              <h2 className="mb-3 text-lg font-semibold text-slate-100">
                {t('detail.reviewsTitle')} ({pr.reviews.length})
              </h2>
              {pr.reviews.length === 0 ? (
                <p className="text-sm text-slate-500">{t('detail.noReviews')}</p>
              ) : (
                <ul className="space-y-3">
                  {pr.reviews.map((review) => (
                    <li
                      key={review.id}
                      className="rounded-xl border border-slate-800 bg-slate-900/40 p-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-sm font-medium text-slate-200">
                          {review.author}
                        </span>
                        <ReviewStateBadge state={review.state} />
                      </div>
                      {review.body ? (
                        <div className="mt-2 rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                          <Markdown size="sm">{review.body}</Markdown>
                        </div>
                      ) : null}
                      {review.submitted_at ? (
                        <p className="mt-2 text-xs text-slate-500">
                          {formatDateTime(review.submitted_at)}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section>
              <h2 className="mb-3 text-lg font-semibold text-slate-100">
                {t('detail.timelineTitle')}
              </h2>
              {pr.timeline.length === 0 ? (
                <p className="text-sm text-slate-500">{t('detail.noEvents')}</p>
              ) : (
                <ol className="space-y-3 border-l border-slate-800 pl-4">
                  {pr.timeline.map((event) => (
                    <li key={event.id} className="relative">
                      <span className="absolute -left-[21px] top-1.5 size-2 rounded-full bg-slate-600" />
                      <p className="text-sm text-slate-300">
                        <span className="font-medium">{event.actor || t('detail.system')}</span>{' '}
                        {event.message}
                      </p>
                      <p className="text-xs text-slate-500">{formatDateTime(event.created_at)}</p>
                    </li>
                  ))}
                </ol>
              )}
            </section>
          </div>
        ) : null}
      </AsyncState>
    </div>
  )
}