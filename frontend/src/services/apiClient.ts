import type {
  ApiErrorBody,
  AuditListResponse,
  AutomationRule,
  AutomationRuleCreate,
  AutomationRuleListResponse,
  AutomationRuleUpdate,
  AutomationStatus,
  DashboardResponse,
  HealthResponse,
  IssueListResponse,
  PullRequestDetail,
  PullRequestListResponse,
  RepositoryConfig,
  RepositoryConfigCreate,
  RepositoryConfigListResponse,
  RepositoryConfigUpdate,
  RepositoryListResponse,
} from '@/types/api'
import type { TFunction } from 'i18next'

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

/**
 * Traduit les erreurs produites côté client (réseau, HTTP générique).
 * Les erreurs du backend portent déjà un message localisé : elles sont
 * telles quelles.
 */
export function apiErrorMessage(error: ApiError, t: TFunction): string {
  if (error.code === 'network_error') {
    return t('api.networkError')
  }
  if (error.code === 'http_error') {
    return t('api.httpError', { status: error.status })
  }
  return error.message
}

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '/api'

function isErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const candidate = value as { error?: unknown }
  return typeof candidate.error === 'object' && candidate.error !== null
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = options
  const headers: Record<string, string> = { Accept: 'application/json' }
  const init: RequestInit = { method, headers, signal }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init)
  } catch {
    throw new ApiError(
      "Impossible de contacter le serveur RepoFlow. Vérifiez qu'il est démarré.",
      0,
      'network_error',
    )
  }

  if (!response.ok) {
    let errorBody: unknown = null
    try {
      errorBody = await response.json()
    } catch {
      // Corps d'erreur illisible : on retombe sur le message générique.
    }
    if (isErrorBody(errorBody)) {
      throw new ApiError(errorBody.error.message, response.status, errorBody.error.code)
    }
    throw new ApiError(
      `La requête a échoué (statut ${response.status}).`,
      response.status,
      'http_error',
    )
  }

  if (response.status === 204) {
    return undefined as T
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
  return request<HealthResponse>('/health', { signal })
}

export function getDashboard(
  signal?: AbortSignal,
  options: Refreshable = {},
): Promise<DashboardResponse> {
  return request<DashboardResponse>(`/v1/dashboard${buildQuery({}, options.refresh)}`, { signal })
}

export function getRepositories(
  signal?: AbortSignal,
  options: Refreshable = {},
): Promise<RepositoryListResponse> {
  return request<RepositoryListResponse>(`/v1/repositories${buildQuery({}, options.refresh)}`, {
    signal,
  })
}

export function getPullRequests(
  params: { repository?: string; search?: string } & Refreshable = {},
  signal?: AbortSignal,
): Promise<PullRequestListResponse> {
  return request<PullRequestListResponse>(
    `/v1/pull-requests${buildQuery(
      { repository: params.repository, search: params.search },
      params.refresh,
    )}`,
    { signal },
  )
}

export function getIssues(
  params: {
    repository?: string
    state?: 'open' | 'closed' | 'all'
    search?: string
  } & Refreshable = {},
  signal?: AbortSignal,
): Promise<IssueListResponse> {
  return request<IssueListResponse>(
    `/v1/issues${buildQuery(
      {
        repository: params.repository,
        state: params.state,
        search: params.search,
      },
      params.refresh,
    )}`,
    { signal },
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
    { signal },
  )
}

export function listRepositoryConfigs(signal?: AbortSignal): Promise<RepositoryConfigListResponse> {
  return request<RepositoryConfigListResponse>('/v1/configs/repositories', { signal })
}

export function createRepositoryConfig(
  payload: RepositoryConfigCreate,
): Promise<RepositoryConfig> {
  return request<RepositoryConfig>('/v1/configs/repositories', { method: 'POST', body: payload })
}

export function updateRepositoryConfig(
  id: number,
  payload: RepositoryConfigUpdate,
): Promise<RepositoryConfig> {
  return request<RepositoryConfig>(`/v1/configs/repositories/${id}`, {
    method: 'PATCH',
    body: payload,
  })
}

export function deleteRepositoryConfig(id: number): Promise<void> {
  return request<void>(`/v1/configs/repositories/${id}`, { method: 'DELETE' })
}

export function listRules(repositoryId: number, signal?: AbortSignal): Promise<AutomationRuleListResponse> {
  return request<AutomationRuleListResponse>(
    `/v1/configs/repositories/${repositoryId}/rules`,
    { signal },
  )
}

export function createRule(
  repositoryId: number,
  payload: AutomationRuleCreate,
): Promise<AutomationRule> {
  return request<AutomationRule>(`/v1/configs/repositories/${repositoryId}/rules`, {
    method: 'POST',
    body: payload,
  })
}

export function updateRule(id: number, payload: AutomationRuleUpdate): Promise<AutomationRule> {
  return request<AutomationRule>(`/v1/configs/rules/${id}`, { method: 'PATCH', body: payload })
}

export function deleteRule(id: number): Promise<void> {
  return request<void>(`/v1/configs/rules/${id}`, { method: 'DELETE' })
}

export function getAutomationStatus(signal?: AbortSignal): Promise<AutomationStatus> {
  return request<AutomationStatus>('/v1/automation/status', { signal })
}

export function setKillSwitch(engaged: boolean): Promise<AutomationStatus> {
  return request<AutomationStatus>('/v1/automation/kill-switch', {
    method: 'POST',
    body: { engaged },
  })
}

export function getAudit(
  params: { event_type?: string; repository?: string } & Refreshable = {},
  signal?: AbortSignal,
): Promise<AuditListResponse> {
  return request<AuditListResponse>(
    `/v1/audit${buildQuery(
      { event_type: params.event_type, repository: params.repository },
      params.refresh,
    )}`,
    { signal },
  )
}
