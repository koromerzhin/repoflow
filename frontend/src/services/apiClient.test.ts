import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { TFunction } from 'i18next'

import {
  ApiError,
  apiErrorMessage,
  createRepositoryConfig,
  deleteRepositoryConfig,
  getAudit,
  getHealth,
  getIssues,
  getPullRequestDetail,
  getPullRequests,
  getSnapshots,
  setKillSwitch,
  updateRule,
} from '@/services/apiClient'

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

  it('signale une erreur HTTP sans corps interprétable', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(new Response('boom', { status: 500 }))

    await expect(getHealth()).rejects.toMatchObject({ code: 'http_error', status: 500 })
  })

  describe('apiErrorMessage', () => {
    const identity = ((key: string) => key) as unknown as TFunction

    it('traduit une erreur réseau', () => {
      const error = new ApiError('network', 0, 'network_error')
      expect(apiErrorMessage(error, identity)).toBe('api.networkError')
    })

    it('traduit une erreur HTTP avec le statut', () => {
      const error = new ApiError('http', 500, 'http_error')
      const t = ((key: string, options?: { status?: number }) =>
        key === 'api.httpError' ? `failed (${options?.status})` : key) as unknown as TFunction
      expect(apiErrorMessage(error, t)).toBe('failed (500)')
    })

    it('conserve le message localisé du backend', () => {
      const error = new ApiError('Ressource absente.', 404, 'not_found')
      expect(apiErrorMessage(error, identity)).toBe('Ressource absente.')
    })
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

  it('construit les filtres de la requête issues', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, data_source: 'demo' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await getIssues({ repository: 'acme/web-app', state: 'closed' })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/issues?repository=acme%2Fweb-app&state=closed',
      expect.anything(),
    )
  })

  it('ajoute le paramètre refresh quand demandé', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, data_source: 'demo' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await getIssues({ state: 'open', refresh: true })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/issues?state=open&refresh=true',
      expect.anything(),
    )
  })

  it('transmet l’offset de pagination dans la requête', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, data_source: 'demo' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await getPullRequests({ offset: 100 })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/pull-requests?offset=100',
      expect.anything(),
    )
  })

  it('construit l’URL du détail de pull request', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ number: 142 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await getPullRequestDetail(142, 'acme/web-app')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/pull-requests/142?repository=acme%2Fweb-app',
      expect.anything(),
    )
  })

  it('construit les filtres de la requête snapshots', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, data_source: 'demo' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await getSnapshots({ repository: 'acme/web-app', since: '2026-01-01', limit: 500 })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/snapshots?repository=acme%2Fweb-app&since=2026-01-01&limit=500',
      expect.anything(),
    )
  })

  it('crée une configuration de dépôt via POST', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ id: 1, full_name: 'acme/web-app' }), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await createRepositoryConfig({ full_name: 'acme/web-app', default_branch: 'main' })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/configs/repositories',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ full_name: 'acme/web-app', default_branch: 'main' }),
      }),
    )
  })

  it('met à jour une règle via PATCH', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ id: 3 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await updateRule(3, { auto_merge_enabled: true })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/configs/rules/3',
      expect.objectContaining({ method: 'PATCH' }),
    )
  })

  it('bascule l’arrêt d’urgence via POST', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ kill_switch_engaged: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const status = await setKillSwitch(true)
    expect(status.kill_switch_engaged).toBe(true)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/automation/kill-switch',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ engaged: true }) }),
    )
  })

  it('supprime un dépôt suivi sans contenu de réponse', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    await expect(deleteRepositoryConfig(7)).resolves.toBeUndefined()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/configs/repositories/7',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })

  it('construit les filtres du journal d’audit', async () => {
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await getAudit({ event_type: 'merge_succeeded', repository: 'acme/web-app' })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/audit?event_type=merge_succeeded&repository=acme%2Fweb-app',
      expect.anything(),
    )
  })
})
