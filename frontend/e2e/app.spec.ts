import { expect, test } from '@playwright/test'

test.describe.configure({ mode: 'serial' })

test('le tableau de bord affiche les compteurs et le bandeau démo', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Tableau de bord' })).toBeVisible()
  await expect(page.getByText(/Mode démonstration/)).toBeVisible()
  await expect(page.getByText('Dépôts suivis', { exact: true })).toBeVisible()
  await expect(page.getByText('Activité récente')).toBeVisible()
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
  await expect(page.getByText(/Échecs intermittents/)).toBeVisible()
  await expect(page.getByText(/réinitialisation de mot de passe/)).toHaveCount(0)
})

test('la langue et le thème persistent', async ({ page }) => {
  await page.goto('/')

  await page.getByRole('combobox', { name: 'Langue' }).selectOption('en')
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
  expect(await page.evaluate(() => localStorage.getItem('i18nextLng'))).toBe('en')

  await page.getByRole('button', { name: 'Toggle theme' }).click()
  await expect(page.locator('html')).toHaveClass(/theme-light/)
  expect(await page.evaluate(() => localStorage.getItem('repoflow-theme'))).toBe('light')
})
