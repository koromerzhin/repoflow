import {
  CircleDot,
  FolderGit2,
  GitPullRequest,
  History,
  LayoutDashboard,
  Workflow,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const navigation = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard, end: true },
  { to: '/repositories', labelKey: 'nav.repositories', icon: FolderGit2, end: false },
  { to: '/pull-requests', labelKey: 'nav.pullRequests', icon: GitPullRequest, end: false },
  { to: '/issues', labelKey: 'nav.issues', icon: CircleDot, end: false },
  { to: '/automations', labelKey: 'nav.automations', icon: Workflow, end: false },
  { to: '/history', labelKey: 'nav.history', icon: History, end: false },
]

interface SidebarProps {
  onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const { t } = useTranslation()
  return (
    <nav aria-label={t('nav.main')} className="flex h-full flex-col gap-1 p-3">
      <div className="mb-4 flex items-center gap-2 px-2 py-2">
        <span className="flex size-9 items-center justify-center rounded-lg bg-sky-500/15 text-lg font-bold text-sky-400 ring-1 ring-sky-500/30">
          RF
        </span>
        <span className="text-lg font-semibold tracking-tight text-slate-50">RepoFlow</span>
      </div>
      {navigation.map(({ to, labelKey, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            [
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition',
              isActive
                ? 'bg-slate-800 text-slate-50'
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200',
            ].join(' ')
          }
        >
          <Icon className="size-4.5 shrink-0" aria-hidden />
          {t(labelKey)}
        </NavLink>
      ))}
    </nav>
  )
}
