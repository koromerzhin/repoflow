import { renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { useDocumentTitle } from '@/hooks/useDocumentTitle'

describe('useDocumentTitle', () => {
  afterEach(() => {
    document.title = 'RepoFlow'
  })

  it('définit le titre du document', () => {
    renderHook(() => useDocumentTitle('Pull requests'))
    expect(document.title).toBe('Pull requests')
  })

  it('met à jour le titre quand il change', () => {
    const { rerender } = renderHook(({ title }) => useDocumentTitle(title), {
      initialProps: { title: 'Dépôts' },
    })
    expect(document.title).toBe('Dépôts')

    rerender({ title: 'Historique' })
    expect(document.title).toBe('Historique')
  })
})