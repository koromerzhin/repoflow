import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'

import { AsyncState } from '@/components/AsyncState'
import { Badge } from '@/components/Badge'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { useResource } from '@/hooks/useAsync'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { auditEventClass, auditEventLabel, formatDateTime } from '@/lib/status'
import { getAudit } from '@/services/apiClient'
import type { AuditEvent } from '@/types/api'

const eventTypeOptions: { value: string; labelKey: string }[] = [
  { value: '', labelKey: 'history.allEvents' },
  { value: 'analysis', labelKey: 'status.audit.analysis' },
  { value: 'analysis_error', labelKey: 'status.audit.analysis_error' },
  { value: 'merge_blocked', labelKey: 'status.audit.merge_blocked' },
  { value: 'merge_skipped', labelKey: 'status.audit.merge_skipped' },
  { value: 'merge_succeeded', labelKey: 'status.audit.merge_succeeded' },
  { value: 'merge_failed', labelKey: 'status.audit.merge_failed' },
]

function payloadSummary(event: AuditEvent, t: TFunction): string | null {
  const payload = event.payload
  if (!payload) {
    return null
  }
  if (typeof payload.reason === 'string') {
    return t('history.reason', { reason: payload.reason })
  }
  if (Array.isArray(payload.blockers) && payload.blockers.length > 0) {
    return t('history.blockers', { list: payload.blockers.join(', ') })
  }
  if (typeof payload.sha === 'string') {
    return t('history.commit', { sha: payload.sha })
  }
  return null
}

export function HistoryPage() {
  const { t } = useTranslation()
  useDocumentTitle(t('history.title'))
  const [eventType, setEventType] = useState('')
  const [repository, setRepository] = useState('')

  const audit = useResource(
    (options, signal) =>
      getAudit(
        {
          event_type: eventType || undefined,
          repository: repository || undefined,
          refresh: options.refresh,
        },
        signal,
      ),
    [eventType, repository],
  )

  const announcement = audit.data ? t('history.announcement', { total: audit.data.total }) : ''

  return (
    <div>
      <PageHeader
        title={t('history.title')}
        description={t('history.description')}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <RefreshButton onClick={audit.refresh} loading={audit.loading} />
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <span className="hidden sm:inline">{t('history.filterType')}</span>
              <select
                value={eventType}
                onChange={(event) => setEventType(event.target.value)}
                className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
              >
                {eventTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {t(option.labelKey)}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <span className="hidden sm:inline">{t('history.filterRepository')}</span>
              <input
                type="text"
                value={repository}
                onChange={(event) => setRepository(event.target.value)}
                placeholder="acme/web-app"
                className="w-44 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
              />
            </label>
          </div>
        }
      />

      <p aria-live="polite" className="sr-only">
        {announcement}
      </p>

      <AsyncState
        loading={audit.loading}
        error={audit.error}
        isEmpty={audit.data?.items.length === 0}
        emptyMessage={t('history.empty')}
        onRetry={audit.reload}
      >
        <ul className="space-y-3">
          {audit.data?.items.map((event) => {
            const summary = payloadSummary(event, t)
            return (
              <li
                key={event.id}
                className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge className={auditEventClass(event.event_type)}>
                        {t(auditEventLabel(event.event_type))}
                      </Badge>
                      {event.repository_full_name ? (
                        <span className="text-sm text-slate-400">
                          {event.repository_full_name}
                          {event.pull_request_number ? `#${event.pull_request_number}` : ''}
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm text-slate-200">{event.message}</p>
                    {summary ? <p className="mt-1 text-xs text-slate-500">{summary}</p> : null}
                  </div>
                  <span className="text-xs text-slate-500">
                    {formatDateTime(event.occurred_at)}
                  </span>
                </div>
              </li>
            )
          })}
        </ul>
      </AsyncState>
    </div>
  )
}
