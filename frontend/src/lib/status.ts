import type {
  CheckState,
  IssueState,
  PullRequestState,
  ReviewDecision,
  ReviewState,
} from '@/types/api'
import i18n from '@/i18n'

export const checkStateLabels: Record<CheckState, string> = {
  success: 'status.check.success',
  failure: 'status.check.failure',
  pending: 'status.check.pending',
  unknown: 'status.check.unknown',
}

export const checkStateClasses: Record<CheckState, string> = {
  success: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  failure: 'bg-red-500/15 text-red-300 ring-red-500/30',
  pending: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  unknown: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
}

export const pullRequestStateLabels: Record<PullRequestState, string> = {
  open: 'status.pr.open',
  draft: 'status.pr.draft',
  closed: 'status.pr.closed',
  merged: 'status.pr.merged',
}

export const pullRequestStateClasses: Record<PullRequestState, string> = {
  open: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  draft: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
  closed: 'bg-red-500/15 text-red-300 ring-red-500/30',
  merged: 'bg-violet-500/15 text-violet-300 ring-violet-500/30',
}

export const reviewDecisionLabels: Record<ReviewDecision, string> = {
  approved: 'status.reviewDecision.approved',
  changes_requested: 'status.reviewDecision.changesRequested',
  review_required: 'status.reviewDecision.reviewRequired',
  none: 'status.reviewDecision.none',
}

export const reviewDecisionClasses: Record<ReviewDecision, string> = {
  approved: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  changes_requested: 'bg-red-500/15 text-red-300 ring-red-500/30',
  review_required: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  none: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
}

export const issueStateLabels: Record<IssueState, string> = {
  open: 'status.issue.open',
  closed: 'status.issue.closed',
}

export const issueStateClasses: Record<IssueState, string> = {
  open: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  closed: 'bg-violet-500/15 text-violet-300 ring-violet-500/30',
}

export const reviewStateLabels: Record<ReviewState, string> = {
  approved: 'status.review.approved',
  changes_requested: 'status.review.changesRequested',
  commented: 'status.review.commented',
  dismissed: 'status.review.dismissed',
  pending: 'status.review.pending',
}

export const reviewStateClasses: Record<ReviewState, string> = {
  approved: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  changes_requested: 'bg-red-500/15 text-red-300 ring-red-500/30',
  commented: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  dismissed: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
  pending: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
}

export const fileStatusLabels: Record<string, string> = {
  added: 'status.file.added',
  modified: 'status.file.modified',
  removed: 'status.file.removed',
  renamed: 'status.file.renamed',
  copied: 'status.file.copied',
}

export const fileStatusClasses: Record<string, string> = {
  added: 'text-emerald-300',
  modified: 'text-sky-300',
  removed: 'text-red-300',
  renamed: 'text-amber-300',
  copied: 'text-violet-300',
}

export const auditEventLabels: Record<string, string> = {
  analysis: 'status.audit.analysis',
  analysis_error: 'status.audit.analysis_error',
  merge_blocked: 'status.audit.merge_blocked',
  merge_skipped: 'status.audit.merge_skipped',
  merge_succeeded: 'status.audit.merge_succeeded',
  merge_failed: 'status.audit.merge_failed',
}

export const auditEventClasses: Record<string, string> = {
  analysis: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  analysis_error: 'bg-red-500/15 text-red-300 ring-red-500/30',
  merge_blocked: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  merge_skipped: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
  merge_succeeded: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  merge_failed: 'bg-red-500/15 text-red-300 ring-red-500/30',
}

export function auditEventLabel(eventType: string): string {
  return auditEventLabels[eventType] ?? eventType
}

export function auditEventClass(eventType: string): string {
  return auditEventClasses[eventType] ?? 'bg-slate-500/15 text-slate-300 ring-slate-500/30'
}

const formatters: Record<string, Intl.DateTimeFormat> = {}

function formatterFor(locale: string): Intl.DateTimeFormat {
  let formatter = formatters[locale]
  if (!formatter) {
    formatter = new Intl.DateTimeFormat(locale, {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
    formatters[locale] = formatter
  }
  return formatter
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return '—'
  }
  return formatterFor(i18n.resolvedLanguage ?? 'fr').format(date)
}
