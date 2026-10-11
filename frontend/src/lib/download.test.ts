import { afterEach, describe, expect, it, vi } from 'vitest'

import { downloadTextFile } from '@/lib/download'

describe('downloadTextFile', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('crée un lien d’export et le déclenche', () => {
    const createObjectURL = vi.fn(() => 'blob:mock')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', {
      createObjectURL,
      revokeObjectURL,
    } as unknown as typeof URL)

    const appendChild = vi.spyOn(document.body, 'appendChild')
    const remove = vi.fn()
    const click = vi.fn()
    const anchor = Object.assign(document.createElement('a'), { click, remove })
    const createElement = vi.spyOn(document, 'createElement').mockReturnValue(anchor)

    downloadTextFile('repoflow-audit.csv', 'a,b', 'text/csv')

    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob))
    expect(createElement).toHaveBeenCalledWith('a')
    expect(anchor.download).toBe('repoflow-audit.csv')
    expect(appendChild).toHaveBeenCalledWith(anchor)
    expect(click).toHaveBeenCalled()
    expect(remove).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock')
  })
})
