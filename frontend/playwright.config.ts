import { defineConfig } from '@playwright/test'

const BACKEND_PORT = 8100
const FRONTEND_PORT = 5183

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    locale: 'fr-FR',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: `npm run dev -- --port ${FRONTEND_PORT} --strictPort`,
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        VITE_PROXY_TARGET: `http://localhost:${BACKEND_PORT}`,
      },
    },
    {
      command: `.venv/bin/uvicorn app.main:app --port ${BACKEND_PORT} --log-level warning`,
      url: `http://localhost:${BACKEND_PORT}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      cwd: '../backend',
      env: {
        REPOFLOW_GITHUB_PROVIDER: 'demo',
        REPOFLOW_DATABASE_URL: 'sqlite:////tmp/repoflow-e2e.db',
        REPOFLOW_AUTO_CREATE_TABLES: 'true',
        REPOFLOW_CACHE_TTL_SECONDS: '0',
      },
    },
  ],
})