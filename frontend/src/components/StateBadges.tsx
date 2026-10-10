import {
  CheckCircle2,
  CircleDashed,
  CircleDot,
  CircleHelp,
  CheckCheck,
  GitMerge,
  GitPullRequest,
  MessageSquareWarning,
  Pencil,
  XCircle,
} from 'lucide-react'

import { useTranslation } from 'react-i18next'

import { Badge } from '@/components/Badge'
import {
  checkStateClasses,
  checkStateLabels,
  issueStateClasses,
  issueStateLabels,
  pullRequestStateClasses,
  pullRequestStateLabels,
  reviewDecisionClasses,
  reviewDecisionLabels,
  reviewStateClasses,
  reviewStateLabels,
} from '@/lib/status'
import type {
  CheckState,
  IssueState,
  PullRequestState,
  ReviewDecision,
  ReviewState,
} from '@/types/api'

export function CheckStateBadge({ state }: { state: CheckState }) {
  const { t } = useTranslation()
  const icon = {
    success: <CheckCircle2 className="size-3.5" aria-hidden />,
    failure: <XCircle className="size-3.5" aria-hidden />,
    pending: <CircleDashed className="size-3.5" aria-hidden />,
    unknown: <CircleHelp className="size-3.5" aria-hidden />,
  }[state]

  return (
    <Badge className={checkStateClasses[state]}>
      {icon}
      {t(checkStateLabels[state])}
    </Badge>
  )
}

export function PullRequestStateBadge({ state }: { state: PullRequestState }) {
  const { t } = useTranslation()
  const icon = {
    open: <GitPullRequest className="size-3.5" aria-hidden />,
    draft: <Pencil className="size-3.5" aria-hidden />,
    closed: <XCircle className="size-3.5" aria-hidden />,
    merged: <GitMerge className="size-3.5" aria-hidden />,
  }[state]

  return (
    <Badge className={pullRequestStateClasses[state]}>
      {icon}
      {t(pullRequestStateLabels[state])}
    </Badge>
  )
}

export function ReviewDecisionBadge({ decision }: { decision: ReviewDecision }) {
  const { t } = useTranslation()
  return (
    <Badge className={reviewDecisionClasses[decision]}>
      <MessageSquareWarning className="size-3.5" aria-hidden />
      {t(reviewDecisionLabels[decision])}
    </Badge>
  )
}

export function IssueStateBadge({ state }: { state: IssueState }) {
  const { t } = useTranslation()
  const icon =
    state === 'open' ? (
      <CircleDot className="size-3.5" aria-hidden />
    ) : (
      <CheckCheck className="size-3.5" aria-hidden />
    )

  return (
    <Badge className={issueStateClasses[state]}>
      {icon}
      {t(issueStateLabels[state])}
    </Badge>
  )
}

export function ReviewStateBadge({ state }: { state: ReviewState }) {
  const { t } = useTranslation()
  return (
    <Badge className={reviewStateClasses[state]}>
      <MessageSquareWarning className="size-3.5" aria-hidden />
      {t(reviewStateLabels[state])}
    </Badge>
  )
}
