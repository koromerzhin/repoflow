import type { Snapshot } from '@/types/api'

/**
 * Série quotidienne agrégée (tous dépôts confondus) pour l'affichage des
 * tendances du tableau de bord.
 */
export interface SnapshotPoint {
  date: string
  repositories: number
  open_pull_requests: number
  pull_requests_ready_to_merge: number
  pull_requests_with_failing_checks: number
  pull_requests_pending_checks: number
  open_issues: number
}

export type SnapshotPointKey = Exclude<keyof SnapshotPoint, 'date'>

/** Clés de compteurs présentes à la fois dans la série et dans les snapshots. */
export type SnapshotCounterKey = Exclude<SnapshotPointKey, 'repositories'>

const COUNTER_KEYS: readonly SnapshotCounterKey[] = [
  'open_pull_requests',
  'pull_requests_ready_to_merge',
  'pull_requests_with_failing_checks',
  'pull_requests_pending_checks',
  'open_issues',
]

/**
 * Agrège les snapshots par dépôt en une série chronologique unique :
 * les compteurs sont sommés et le nombre de dépôts distincts est compté
 * pour chaque date. La série est triée par date croissante.
 */
export function aggregateSnapshots(items: Snapshot[]): SnapshotPoint[] {
  const byDate = new Map<string, SnapshotPoint & { repositoriesSet: Set<string> }>()
  for (const item of items) {
    let point = byDate.get(item.snapshot_date)
    if (!point) {
      point = {
        date: item.snapshot_date,
        repositories: 0,
        open_pull_requests: 0,
        pull_requests_ready_to_merge: 0,
        pull_requests_with_failing_checks: 0,
        pull_requests_pending_checks: 0,
        open_issues: 0,
        repositoriesSet: new Set<string>(),
      }
      byDate.set(item.snapshot_date, point)
    }
    point.repositoriesSet.add(item.repository_full_name)
    for (const key of COUNTER_KEYS) {
      point[key] += item[key]
    }
  }

  return [...byDate.values()]
    .map((point) => {
      const { repositoriesSet, ...counters } = point
      return { ...counters, repositories: repositoriesSet.size }
    })
    .sort((a, b) => a.date.localeCompare(b.date))
}

/** Extrait la série de valeurs d'un compteur donné. */
export function seriesFor(snapshots: SnapshotPoint[], key: SnapshotPointKey): number[] {
  return snapshots.map((point) => point[key])
}
