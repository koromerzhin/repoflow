import { CircleAlert, Menu, ShieldCheck, ShieldX, X } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Outlet, useLocation } from 'react-router-dom'

import { Badge } from '@/components/Badge'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { Sidebar } from '@/components/Sidebar'
import { useAsync } from '@/hooks/useAsync'
import { getHealth } from '@/services/apiClient'

export function AppLayout() {
  const { t } = useTranslation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
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

      {sidebarOpen ? (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            aria-label={t('app.closeMenu')}
            className="absolute inset-0 bg-slate-950/70"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-64 border-r border-slate-800 bg-slate-950">
            <div className="flex justify-end p-2">
              <button
                type="button"
                aria-label={t('app.closeMenu')}
                onClick={() => setSidebarOpen(false)}
                className="rounded-md p-2 text-slate-400 hover:bg-slate-900 hover:text-slate-100"
              >
                <X className="size-5" aria-hidden />
              </button>
            </div>
            <Sidebar onNavigate={() => setSidebarOpen(false)} />
          </div>
        </div>
      ) : null}

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

        <main id="contenu" key={location.pathname} className="mx-auto max-w-6xl px-4 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
