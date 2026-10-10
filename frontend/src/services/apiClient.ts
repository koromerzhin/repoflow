import type {
  ApiErrorBody,
  DashboardResponse,
  HealthResponse,
  PullRequestListResponse,
  RepositoryListResponse,
} from '@/types/api'

/**
 * Erreur normalisée renvoyée par le client HTTP.
 * Aucun secret ne doit jamais transiter par le frontend.
 */
export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(message: string, status: number, code: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '/api'

function isErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const candidate = value as { error?: unknown }
  return typeof candidate.error === 'object' && candidate.error !== null
}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: 'application/json' },
      signal,
    })
  } catch {
    throw new ApiError(
      "Impossible de contacter le serveur RepoFlow. Vérifiez qu'il est démarré.",
      0,
      'network_error',
    )
  }

  if (!response.ok) {
    let body: unknown = null
    try {
      body = await response.json()
    } catch {
      // Corps d'erreur illisible : on retombe sur le message générique.
    }
    if (isErrorBody(body)) {
      throw new ApiError(body.error.message, response.status, body.error.code)
    }
    throw new ApiError(
      `La requête a échoué (statut ${response.status}).`,
      response.status,
      'http_error',
    )
  }

  return (await response.json()) as T
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>('/health', signal)
}

export function getDashboard(signal?: AbortSignal): Promise<DashboardResponse> {
  return request<DashboardResponse>('/v1/dashboard', signal)
}

export function getRepositories(signal?: AbortSignal): Promise<RepositoryListResponse> {
  return request<RepositoryListResponse>('/v1/repositories', signal)
}

export function getPullRequests(
  params: { repository?: string } = {},
  signal?: AbortSignal,
): Promise<PullRequestListResponse> {
  const search = new URLSearchParams()
  if (params.repository) {
    search.set('repository', params.repository)
  }
  const query = search.toString()
  return request<PullRequestListResponse>(
    `/v1/pull-requests${query ? `?${query}` : ''}`,
    signal,
  )
}
