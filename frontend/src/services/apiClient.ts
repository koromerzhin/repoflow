import type {
  ApiErrorBody,
  DashboardResponse,
  HealthResponse,
  IssueListResponse,
  PullRequestDetail,
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

export interface Refreshable {
  refresh?: boolean
}

function buildQuery(params: Record<string, string | undefined>, refresh?: boolean): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      search.set(key, value)
    }
  }
  if (refresh) {
    search.set('refresh', 'true')
  }
  const query = search.toString()
  return query ? `?${query}` : ''
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>('/health', signal)
}

export function getDashboard(
  signal?: AbortSignal,
  options: Refreshable = {},
): Promise<DashboardResponse> {
  return request<DashboardResponse>(`/v1/dashboard${buildQuery({}, options.refresh)}`, signal)
}

export function getRepositories(
  signal?: AbortSignal,
  options: Refreshable = {},
): Promise<RepositoryListResponse> {
  return request<RepositoryListResponse>(
    `/v1/repositories${buildQuery({}, options.refresh)}`,
    signal,
  )
}

export function getPullRequests(
  params: { repository?: string } & Refreshable = {},
  signal?: AbortSignal,
): Promise<PullRequestListResponse> {
  return request<PullRequestListResponse>(
    `/v1/pull-requests${buildQuery({ repository: params.repository }, params.refresh)}`,
    signal,
  )
}

export function getIssues(
  params: { repository?: string; state?: 'open' | 'closed' | 'all' } & Refreshable = {},
  signal?: AbortSignal,
): Promise<IssueListResponse> {
  return request<IssueListResponse>(
    `/v1/issues${buildQuery(
      { repository: params.repository, state: params.state },
      params.refresh,
    )}`,
    signal,
  )
}

export function getPullRequestDetail(
  number: number,
  repository: string,
  signal?: AbortSignal,
  options: Refreshable = {},
): Promise<PullRequestDetail> {
  return request<PullRequestDetail>(
    `/v1/pull-requests/${number}${buildQuery({ repository }, options.refresh)}`,
    signal,
  )
}
