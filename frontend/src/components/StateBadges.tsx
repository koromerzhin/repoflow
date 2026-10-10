import {
  CheckCircle2,
  CircleDashed,
  CircleHelp,
  GitMerge,
  GitPullRequest,
  MessageSquareWarning,
  Pencil,
  XCircle,
} from 'lucide-react'

import { Badge } from '@/components/Badge'
import {
  checkStateClasses,
  checkStateLabels,
  pullRequestStateClasses,
  pullRequestStateLabels,
  reviewDecisionClasses,
  reviewDecisionLabels,
} from '@/lib/status'
import type { CheckState, PullRequestState, ReviewDecision } from '@/types/api'

export function CheckStateBadge({ state }: { state: CheckState }) {
  const icon = {
    success: <CheckCircle2 className="size-3.5" aria-hidden />,
    failure: <XCircle className="size-3.5" aria-hidden />,
    pending: <CircleDashed className="size-3.5" aria-hidden />,
    unknown: <CircleHelp className="size-3.5" aria-hidden />,
  }[state]

  return (
    <Badge className={checkStateClasses[state]}>
      {icon}
      {checkStateLabels[state]}
    </Badge>
  )
}

export function PullRequestStateBadge({ state }: { state: PullRequestState }) {
  const icon = {
    open: <GitPullRequest className="size-3.5" aria-hidden />,
    draft: <Pencil className="size-3.5" aria-hidden />,
    closed: <XCircle className="size-3.5" aria-hidden />,
    merged: <GitMerge className="size-3.5" aria-hidden />,
  }[state]

  return (
    <Badge className={pullRequestStateClasses[state]}>
      {icon}
      {pullRequestStateLabels[state]}
    </Badge>
  )
}

export function ReviewDecisionBadge({ decision }: { decision: ReviewDecision }) {
  return (
    <Badge className={reviewDecisionClasses[decision]}>
      <MessageSquareWarning className="size-3.5" aria-hidden />
      {reviewDecisionLabels[decision]}
    </Badge>
  )
}
