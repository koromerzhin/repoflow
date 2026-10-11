import { CircleAlert, Gauge, LogOut, Menu, ShieldCheck, ShieldX } from 'lucide-react'
import { Suspense, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Outlet, useLocation } from 'react-router-dom'

import { Badge } from '@/components/Badge'
import { Drawer } from '@/components/Drawer'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { PageLoader } from '@/components/PageLoader'
import { Sidebar } from '@/components/Sidebar'
import { ThemeToggle } from '@/components/ThemeToggle'
import { useAsync } from '@/hooks/useAsync'
import { useAuth } from '@/hooks/useAuth'
import { getHealth } from '@/services/apiClient'

const GITHUB_QUOTA_LOW_THRESHOLD = 100

export function AppLayout() {
  const { t } = useTranslation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const { token, logout } = useAuth()

  useEffect(() => {
    mainRef.current?.focus()
  }, [location.pathname])

  const { data: health } = useAsync(getHealth, [])

  const isDemo = health?.data_source === 'demo'
  const healthOk = health?.status === 'ok'

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <a
        href="#contenu"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded-md focus:bg-sky-600 focus:px-3 focus:py-2 focus:text-sm focus:text-white"
      >
        {t('app.skipToContent')}
      </a>

      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-slate-800 bg-slate-950/80 md:block">
        <Sidebar />
      </aside>

      <Drawer
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        label={t('nav.main')}
      >
        <Sidebar onNavigate={() => setSidebarOpen(false)} />
      </Drawer>

      <div className="md:pl-60">
        <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-slate-800 bg-slate-950/85 px-4 py-3 backdrop-blur">
          <button
            type="button"
            aria-label={t('app.openMenu')}
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-2 text-slate-300 hover:bg-slate-900 md:hidden"
          >
            <Menu className="size-5" aria-hidden />
          </button>

          <div className="hidden text-sm text-slate-400 md:block">
            {t('app.subtitle')}
          </div>

          <div className="flex items-center gap-2">
            {health ? (
              <Badge
                className={
                  healthOk
                    ? 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30'
                    : 'bg-amber-500/15 text-amber-300 ring-amber-500/30'
                }
              >
                {healthOk ? (
                  <ShieldCheck className="size-3.5" aria-hidden />
                ) : (
                  <ShieldX className="size-3.5" aria-hidden />
                )}
                {healthOk ? t('app.apiOperational') : t('app.apiDegraded')}
              </Badge>
            ) : null}
            {health?.kill_switch_engaged ? (
              <Badge className="bg-red-500/15 text-red-300 ring-red-500/30">
                <CircleAlert className="size-3.5" aria-hidden />
                {t('app.killSwitchActive')}
              </Badge>
            ) : null}
            {health?.github_rate_limit?.remaining != null &&
            health.github_rate_limit.remaining <= GITHUB_QUOTA_LOW_THRESHOLD ? (
              <Badge className="bg-amber-500/15 text-amber-300 ring-amber-500/30">
                <Gauge className="size-3.5" aria-hidden />
                {t('app.githubQuota', { remaining: health.github_rate_limit.remaining })}
              </Badge>
            ) : null}
            {token ? (
              <button
                type="button"
                aria-label={t('auth.logout')}
                onClick={() => {
                  logout()
                  window.location.reload()
                }}
                className="rounded-md border border-slate-700 bg-slate-900 p-1.5 text-slate-300 transition hover:border-red-600 hover:text-red-300"
              >
                <LogOut className="size-4" aria-hidden />
              </button>
            ) : null}
            <ThemeToggle />
            <LanguageSwitcher />
          </div>
        </header>

        {isDemo ? (
          <div
            role="note"
            className="flex items-center gap-2 border-b border-amber-900/50 bg-amber-950/30 px-4 py-2 text-sm text-amber-200"
          >
            <CircleAlert className="size-4 shrink-0" aria-hidden />
            <span>{t('app.demoBanner')}</span>
          </div>
        ) : null}

        <main
          id="contenu"
          ref={mainRef}
          tabIndex={-1}
          key={location.pathname}
          className="mx-auto max-w-6xl px-4 py-8 focus:outline-none"
        >
          <ErrorBoundary>
            <Suspense fallback={<PageLoader />}>
              <Outlet />
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
