import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

import { PageLoader } from '@/components/PageLoader'
import { AppLayout } from '@/layouts/AppLayout'

const DashboardPage = lazy(() =>
  import('@/pages/DashboardPage').then((module) => ({ default: module.DashboardPage })),
)
const RepositoriesPage = lazy(() =>
  import('@/pages/RepositoriesPage').then((module) => ({
    default: module.RepositoriesPage,
  })),
)
const PullRequestsPage = lazy(() =>
  import('@/pages/PullRequestsPage').then((module) => ({
    default: module.PullRequestsPage,
  })),
)
const PullRequestDetailPage = lazy(() =>
  import('@/pages/PullRequestDetailPage').then((module) => ({
    default: module.PullRequestDetailPage,
  })),
)
const IssuesPage = lazy(() =>
  import('@/pages/IssuesPage').then((module) => ({ default: module.IssuesPage })),
)
const AutomationsPage = lazy(() =>
  import('@/pages/AutomationsPage').then((module) => ({
    default: module.AutomationsPage,
  })),
)
const HistoryPage = lazy(() =>
  import('@/pages/HistoryPage').then((module) => ({ default: module.HistoryPage })),
)
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((module) => ({ default: module.NotFoundPage })),
)

export function App() {
  return (
    <Suspense fallback={<PageLoader />}>
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
    </Suspense>
  )
}