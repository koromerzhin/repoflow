/**
 * Types TypeScript correspondant aux réponses de l'API RepoFlow.
 * Ces types reflètent les schémas Pydantic du backend.
 */

export type DataSource = 'demo' | 'github'

export type CheckState = 'success' | 'failure' | 'pending' | 'unknown'

export type PullRequestState = 'open' | 'draft' | 'closed' | 'merged'

export type ReviewDecision =
  | 'approved'
  | 'changes_requested'
  | 'review_required'
  | 'none'

export interface ProviderInfo {
  name: string
  is_demo: boolean
  requires_token: boolean
}

export interface HealthResponse {
  status: 'ok' | 'degraded'
  app: string
  version: string
  environment: string
  timestamp: string
  data_source: DataSource
  database: 'ok' | 'unavailable' | 'not_checked'
  kill_switch_engaged: boolean
}

export interface DashboardCounters {
  repositories: number
  open_pull_requests: number
  pull_requests_ready_to_merge: number
  pull_requests_with_failing_checks: number
  pull_requests_pending_checks: number
  open_issues: number
}

export interface ActivityItem {
  id: string
  event_type: string
  message: string
  repository_full_name: string | null
  occurred_at: string
}

export interface DashboardResponse {
  generated_at: string
  data_source: DataSource
  provider: ProviderInfo
  counters: DashboardCounters
  recent_activity: ActivityItem[]
}

export interface Repository {
  id: string
  owner: string
  name: string
  full_name: string
  default_branch: string
  private: boolean
  open_issues_count: number
  open_pull_requests_count: number
  last_updated: string
  html_url: string
  is_demo: boolean
}

export interface RepositoryListResponse {
  items: Repository[]
  total: number
  data_source: DataSource
}

export interface Check {
  name: string
  state: CheckState
  conclusion: string | null
  required: boolean
  details_url: string | null
}

export interface MergeBlocker {
  code: string
  message: string
}

export interface MergeEligibility {
  eligible: boolean
  blockers: MergeBlocker[]
}

export interface PullRequest {
  id: string
  number: number
  repository_full_name: string
  title: string
  author: string
  source_branch: string
  target_branch: string
  state: PullRequestState
  is_draft: boolean
  checks: Check[]
  checks_state: CheckState
  review_decision: ReviewDecision
  mergeable: boolean
  changed_files: number
  additions: number
  deletions: number
  merge_eligibility: MergeEligibility
  created_at: string
  updated_at: string
  html_url: string
  is_demo: boolean
}

export interface PullRequestListResponse {
  items: PullRequest[]
  total: number
  data_source: DataSource
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    details?: unknown
  }
}
