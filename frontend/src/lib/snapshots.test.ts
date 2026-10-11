import { describe, expect, it } from 'vitest'

import { aggregateSnapshots, seriesFor } from '@/lib/snapshots'
import type { Snapshot } from '@/types/api'

function snapshot(overrides: Partial<Snapshot>): Snapshot {
  return {
    id: 1,
    repository_full_name: 'acme/web-app',
    snapshot_date: '2026-01-01',
    data_source: 'demo',
    open_pull_requests: 0,
    pull_requests_ready_to_merge: 0,
    pull_requests_with_failing_checks: 0,
    pull_requests_pending_checks: 0,
    open_issues: 0,
    ...overrides,
  }
}

describe('aggregateSnapshots', () => {
  it('somme les compteurs de tous les dépôts par date', () => {
    const points = aggregateSnapshots([
      snapshot({ snapshot_date: '2026-01-01', open_pull_requests: 2, open_issues: 5 }),
      snapshot({
        id: 2,
        repository_full_name: 'acme/api',
        snapshot_date: '2026-01-01',
        open_pull_requests: 3,
        open_issues: 1,
      }),
      snapshot({ id: 3, snapshot_date: '2026-01-02', open_pull_requests: 4, open_issues: 6 }),
    ])

    expect(points).toHaveLength(2)
    expect(points[0]).toMatchObject({ date: '2026-01-01', open_pull_requests: 5, open_issues: 6 })
    expect(points[1]).toMatchObject({ date: '2026-01-02', open_pull_requests: 4, open_issues: 6 })
  })

  it('compte les dépôts distincts par date', () => {
    const points = aggregateSnapshots([
      snapshot({ snapshot_date: '2026-01-01', repository_full_name: 'a' }),
      snapshot({ id: 2, snapshot_date: '2026-01-01', repository_full_name: 'b' }),
      // Doublon de dépôt le même jour : ne compte qu'une fois.
      snapshot({ id: 3, snapshot_date: '2026-01-01', repository_full_name: 'a' }),
      snapshot({ id: 4, snapshot_date: '2026-01-02', repository_full_name: 'c' }),
    ])

    expect(points.map((point) => point.repositories)).toEqual([2, 1])
  })

  it('trie la série par date croissante quel que soit l’ordre d’entrée', () => {
    const points = aggregateSnapshots([
      snapshot({ snapshot_date: '2026-01-03' }),
      snapshot({ snapshot_date: '2026-01-01' }),
      snapshot({ snapshot_date: '2026-01-02' }),
    ])
    expect(points.map((point) => point.date)).toEqual([
      '2026-01-01',
      '2026-01-02',
      '2026-01-03',
    ])
  })

  it('renvoie une série vide sans snapshot', () => {
    expect(aggregateSnapshots([])).toEqual([])
  })

  it('extrait la série d’un compteur', () => {
    const points = aggregateSnapshots([
      snapshot({ snapshot_date: '2026-01-01', open_issues: 3 }),
      snapshot({ snapshot_date: '2026-01-02', open_issues: 8 }),
    ])
    expect(seriesFor(points, 'open_issues')).toEqual([3, 8])
  })
})
