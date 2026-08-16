import { createBrowserRouter } from 'react-router-dom'
import { RootLayout } from './pages/RootLayout'
import { DashboardPage } from './pages/DashboardPage'
import { TransactionsPage } from './pages/TransactionsPage'
import { TransactionFormPage } from './pages/TransactionFormPage'
import { ImportPage } from './pages/ImportPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'transactions', element: <TransactionsPage /> },
      { path: 'transactions/new', element: <TransactionFormPage /> },
      { path: 'transactions/:id/edit', element: <TransactionFormPage /> },
      { path: 'import', element: <ImportPage /> },
    ],
  },
])
