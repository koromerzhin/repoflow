import { Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/layouts/AppLayout'
import { AutomationsPage } from '@/pages/AutomationsPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { IssuesPage } from '@/pages/IssuesPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { PullRequestDetailPage } from '@/pages/PullRequestDetailPage'
import { PullRequestsPage } from '@/pages/PullRequestsPage'
import { RepositoriesPage } from '@/pages/RepositoriesPage'

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="repositories" element={<RepositoriesPage />} />
        <Route path="pull-requests" element={<PullRequestsPage />} />
        <Route path="pull-requests/:number" element={<PullRequestDetailPage />} />
        <Route path="issues" element={<IssuesPage />} />
        <Route path="automations" element={<AutomationsPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
