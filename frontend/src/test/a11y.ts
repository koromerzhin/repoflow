import axe from 'axe-core'
import { expect } from 'vitest'

/**
 * Vérifie l'absence de violations d'accessibilité détectables par axe.
 * Le contraste des couleurs est désactivé : il dépend du rendu réel et fait
 * l'objet d'un audit dédié (docs/ameliorations.md, P3.28).
 */
export async function expectNoA11yViolations(
  container: HTMLElement = document.body,
): Promise<void> {
  const results = await axe.run(container, {
    rules: {
      'color-contrast': { enabled: false },
    },
  })
  const violations = results.violations.map((violation) => violation.id)
  expect(violations).toEqual([])
}
