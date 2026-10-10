import {
  FolderGit2,
  GitPullRequest,
  History,
  LayoutDashboard,
  Workflow,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

const navigation = [
  { to: '/', label: 'Tableau de bord', icon: LayoutDashboard, end: true },
  { to: '/repositories', label: 'Dépôts', icon: FolderGit2, end: false },
  { to: '/pull-requests', label: 'Pull requests', icon: GitPullRequest, end: false },
  { to: '/automations', label: 'Automatisations', icon: Workflow, end: false },
  { to: '/history', label: 'Historique', icon: History, end: false },
]

interface SidebarProps {
  onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
  return (
    <nav aria-label="Navigation principale" className="flex h-full flex-col gap-1 p-3">
      <div className="mb-4 flex items-center gap-2 px-2 py-2">
        <span className="flex size-9 items-center justify-center rounded-lg bg-sky-500/15 text-lg font-bold text-sky-400 ring-1 ring-sky-500/30">
          RF
        </span>
        <span className="text-lg font-semibold tracking-tight text-slate-50">RepoFlow</span>
      </div>
      {navigation.map(({ to, label, icon: Icon, end }) => (
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
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
