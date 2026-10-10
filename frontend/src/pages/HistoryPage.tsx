import { useState } from 'react'

import { AsyncState } from '@/components/AsyncState'
import { Badge } from '@/components/Badge'
import { PageHeader } from '@/components/PageHeader'
import { RefreshButton } from '@/components/RefreshButton'
import { useResource } from '@/hooks/useAsync'
import { auditEventClass, auditEventLabel, formatDateTime } from '@/lib/status'
import { getAudit } from '@/services/apiClient'
import type { AuditEvent } from '@/types/api'

const eventTypeOptions: { value: string; label: string }[] = [
  { value: '', label: 'Tous les événements' },
  { value: 'analysis', label: 'Analyse' },
  { value: 'analysis_error', label: 'Erreur d’analyse' },
  { value: 'merge_blocked', label: 'Fusion bloquée' },
  { value: 'merge_skipped', label: 'Fusion différée' },
  { value: 'merge_succeeded', label: 'Fusion réussie' },
  { value: 'merge_failed', label: 'Échec de fusion' },
]

function payloadSummary(event: AuditEvent): string | null {
  const payload = event.payload
  if (!payload) {
    return null
  }
  if (typeof payload.reason === 'string') {
    return `Motif : ${payload.reason}`
  }
  if (Array.isArray(payload.blockers) && payload.blockers.length > 0) {
    return `Blocages : ${payload.blockers.join(', ')}`
  }
  if (typeof payload.sha === 'string') {
    return `Commit : ${payload.sha}`
  }
  return null
}

export function HistoryPage() {
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

  const announcement = audit.data ? `${audit.data.total} événement(s) journalisé(s).` : ''

  return (
    <div>
      <PageHeader
        title="Historique"
        description="Journal d'audit des analyses, décisions et tentatives de fusion. Lecture seule."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <RefreshButton onClick={audit.refresh} loading={audit.loading} />
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <span className="hidden sm:inline">Type</span>
              <select
                value={eventType}
                onChange={(event) => setEventType(event.target.value)}
                className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
              >
                {eventTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <span className="hidden sm:inline">Dépôt</span>
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
        emptyMessage="Aucun événement dans le journal pour ce filtre."
        onRetry={audit.reload}
      >
        <ul className="space-y-3">
          {audit.data?.items.map((event) => {
            const summary = payloadSummary(event)
            return (
              <li
                key={event.id}
                className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge className={auditEventClass(event.event_type)}>
                        {auditEventLabel(event.event_type)}
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
