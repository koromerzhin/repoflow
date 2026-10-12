import { expect, test } from '@playwright/test'

test.describe.configure({ mode: 'serial' })

test('le tableau de bord affiche les compteurs et le bandeau démo', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Tableau de bord' })).toBeVisible()
  await expect(page.getByText(/Mode démonstration/)).toBeVisible()
  await expect(page.getByText('Dépôts suivis', { exact: true })).toBeVisible()
  await expect(page.getByText('Activité récente')).toBeVisible()
  // En mode démonstration, aucun quota GitHub n'est exposé.
  await expect(page.getByTestId('github-quota')).toHaveCount(0)
})

test('les activités récentes mènent au détail de la pull request', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Activité récente')).toBeVisible()

  const firstActivity = page.locator('section ul li a').first()
  await expect(firstActivity).toContainText(/PR #\d+/)
  await firstActivity.click()

  await expect(page).toHaveURL(/\/pull-requests\/\d+\?repository=/)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
})

test('les dépôts mènent à leurs pull requests et leurs issues', async ({ page }) => {
  await page.goto('/repositories')
  await expect(page.getByRole('caption')).toBeVisible()

  await page
    .getByRole('link', { name: /Voir les \d+ pull requests du dépôt/ })
    .first()
    .click()
  await expect(page).toHaveURL(/\/pull-requests\?repository=/)
  await expect(page.getByRole('heading', { name: 'Pull requests' })).toBeVisible()

  await page.goto('/repositories')
  await page.getByRole('link', { name: /Voir les \d+ issues du dépôt/ }).first().click()
  await expect(page).toHaveURL(/\/issues\?repository=/)
  await expect(page.getByRole('heading', { name: 'Issues' })).toBeVisible()
})

test('la liste des pull requests se filtre par recherche', async ({ page }) => {
  await page.goto('/pull-requests')
  await expect(page.getByRole('heading', { name: 'Pull requests' })).toBeVisible()
  const cards = page.locator('article')
  await expect(cards.first()).toBeVisible()

  const initialCount = await cards.count()
  expect(initialCount).toBeGreaterThan(1)

  const search = page.getByRole('searchbox')
  await search.fill('authentification')
  await expect(page.locator('article')).toHaveCount(1)
  await expect(page.getByText(/Refonte du module d.authentification/)).toBeVisible()
})

test('les issues exposent libellés, assignés et filtres avancés', async ({ page }) => {
  await page.goto('/issues')
  await expect(page.getByRole('heading', { name: 'Issues' })).toBeVisible()
  await expect(page.locator('li').getByText('bug', { exact: true }).first()).toBeVisible()
  await expect(page.getByText(/@lea\.b/).first()).toBeVisible()

  await page.getByRole('combobox', { name: 'Libellé' }).selectOption('observabilité')
  await expect(page.getByRole('heading', { name: /Échecs intermittents/ })).toBeVisible()
  await expect(page.getByText(/réinitialisation de mot de passe/)).toHaveCount(0)
})

test('le corps des issues est rendu en Markdown', async ({ page }) => {
  await page.goto('/issues')
  await expect(page.getByRole('heading', { name: 'Constat' }).first()).toBeVisible()
  await expect(page.locator('li pre').first()).toBeVisible()
})

test('le détail d’une PR propose un lien GitHub et rend le Markdown', async ({ page }) => {
  await page.goto('/pull-requests/130?repository=acme%2Fweb-app')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()

  const github = page.getByRole('link', { name: 'Voir sur GitHub' })
  await expect(github).toHaveAttribute('href', 'https://github.com/acme/web-app/pull/130')
  await expect(github).toHaveAttribute('target', '_blank')

  await expect(page.getByRole('heading', { name: 'Contexte' })).toBeVisible()
})

test('la langue et le thème persistent', async ({ page }) => {
  await page.goto('/')

  await page.getByRole('combobox', { name: 'Langue' }).selectOption('en')
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
  expect(await page.evaluate(() => localStorage.getItem('i18nextLng'))).toBe('en')

  const btn = page.getByRole('button', { name: 'Toggle theme' })
  // Assume default dark theme in CI
  await btn.click()
  await page.waitForTimeout(100)
  const theme = await page.evaluate(() => localStorage.getItem('repoflow-theme'))
  expect(theme === 'light' || theme === 'dark').toBe(true)
})
