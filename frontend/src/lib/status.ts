import type {
  CheckState,
  IssueState,
  PullRequestState,
  ReviewDecision,
  ReviewState,
} from '@/types/api'

export const checkStateLabels: Record<CheckState, string> = {
  success: 'Réussi',
  failure: 'Échoué',
  pending: 'En cours',
  unknown: 'Inconnu',
}

export const checkStateClasses: Record<CheckState, string> = {
  success: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  failure: 'bg-red-500/15 text-red-300 ring-red-500/30',
  pending: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  unknown: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
}

export const pullRequestStateLabels: Record<PullRequestState, string> = {
  open: 'Ouverte',
  draft: 'Brouillon',
  closed: 'Fermée',
  merged: 'Fusionnée',
}

export const pullRequestStateClasses: Record<PullRequestState, string> = {
  open: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  draft: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
  closed: 'bg-red-500/15 text-red-300 ring-red-500/30',
  merged: 'bg-violet-500/15 text-violet-300 ring-violet-500/30',
}

export const reviewDecisionLabels: Record<ReviewDecision, string> = {
  approved: 'Approuvée',
  changes_requested: 'Modifications demandées',
  review_required: 'Revue requise',
  none: 'Aucune revue',
}

export const reviewDecisionClasses: Record<ReviewDecision, string> = {
  approved: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  changes_requested: 'bg-red-500/15 text-red-300 ring-red-500/30',
  review_required: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  none: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
}

export const issueStateLabels: Record<IssueState, string> = {
  open: 'Ouverte',
  closed: 'Fermée',
}

export const issueStateClasses: Record<IssueState, string> = {
  open: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  closed: 'bg-violet-500/15 text-violet-300 ring-violet-500/30',
}

export const reviewStateLabels: Record<ReviewState, string> = {
  approved: 'Approuvée',
  changes_requested: 'Modifications demandées',
  commented: 'Commentée',
  dismissed: 'Rejetée',
  pending: 'En attente',
}

export const reviewStateClasses: Record<ReviewState, string> = {
  approved: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  changes_requested: 'bg-red-500/15 text-red-300 ring-red-500/30',
  commented: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  dismissed: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
  pending: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
}

export const fileStatusLabels: Record<string, string> = {
  added: 'Ajouté',
  modified: 'Modifié',
  removed: 'Supprimé',
  renamed: 'Renommé',
  copied: 'Copié',
}

export const fileStatusClasses: Record<string, string> = {
  added: 'text-emerald-300',
  modified: 'text-sky-300',
  removed: 'text-red-300',
  renamed: 'text-amber-300',
  copied: 'text-violet-300',
}

export const auditEventLabels: Record<string, string> = {
  analysis: 'Analyse',
  analysis_error: 'Erreur d’analyse',
  merge_blocked: 'Fusion bloquée',
  merge_skipped: 'Fusion différée',
  merge_succeeded: 'Fusion réussie',
  merge_failed: 'Échec de fusion',
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

const dateFormatter = new Intl.DateTimeFormat('fr-FR', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return '—'
  }
  return dateFormatter.format(date)
}
