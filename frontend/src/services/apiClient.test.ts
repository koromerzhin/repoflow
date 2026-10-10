import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, getHealth, getPullRequests } from '@/services/apiClient'

const healthPayload = {
  status: 'ok',
  app: 'RepoFlow',
  version: '0.1.0',
  environment: 'test',
  timestamp: '2026-01-01T00:00:00Z',
  data_source: 'demo',
  database: 'ok',
  kill_switch_engaged: false,
} as const

describe('apiClient', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('retourne les données en cas de succès', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify(healthPayload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const result = await getHealth()
    expect(result.app).toBe('RepoFlow')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/health',
      expect.objectContaining({ headers: { Accept: 'application/json' } }),
    )
  })

  it("convertit une réponse d'erreur en ApiError", async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockImplementation(async () =>
      new Response(
        JSON.stringify({ error: { code: 'not_found', message: 'Ressource absente.' } }),
        { status: 404, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    await expect(getHealth()).rejects.toBeInstanceOf(ApiError)
    await expect(getHealth()).rejects.toMatchObject({
      status: 404,
      code: 'not_found',
      message: 'Ressource absente.',
    })
  })

  it('signale une erreur réseau', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(getHealth()).rejects.toMatchObject({ code: 'network_error', status: 0 })
  })

  it('construit le filtre de dépôt dans la requête', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, data_source: 'demo' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await getPullRequests({ repository: 'acme/web-app' })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/pull-requests?repository=acme%2Fweb-app',
      expect.anything(),
    )
  })
})
