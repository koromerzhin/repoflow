import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll } from 'vitest'

import i18n from '@/i18n'

beforeAll(async () => {
  // Tests déterministes en français, quelle que soit la langue du navigateur.
  await i18n.changeLanguage('fr')
})

afterEach(() => {
  cleanup()
})