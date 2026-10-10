import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import {
  CheckStateBadge,
  PullRequestStateBadge,
  ReviewDecisionBadge,
} from '@/components/StateBadges'

describe('StateBadges', () => {
  it("affiche le libellé français d'un check réussi", () => {
    render(<CheckStateBadge state="success" />)
    expect(screen.getByText('Réussi')).toBeInTheDocument()
  })

  it('n\'affiche jamais un check inconnu comme réussi', () => {
    render(<CheckStateBadge state="unknown" />)
    expect(screen.getByText('Inconnu')).toBeInTheDocument()
    expect(screen.queryByText('Réussi')).not.toBeInTheDocument()
  })

  it('affiche l\'état d\'une pull request', () => {
    render(<PullRequestStateBadge state="draft" />)
    expect(screen.getByText('Brouillon')).toBeInTheDocument()
  })

  it('affiche la décision de revue', () => {
    render(<ReviewDecisionBadge decision="changes_requested" />)
    expect(screen.getByText('Modifications demandées')).toBeInTheDocument()
  })
})
