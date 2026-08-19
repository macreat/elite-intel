import { Outlet } from 'react-router-dom'
import { Sidebar } from '../components/layout/Sidebar'

export function RootLayout() {
  return (
    <div className="min-h-screen bg-navy-900">
      <Sidebar />
      <main className="p-4 pb-20 md:p-6">
        <Outlet />
      </main>
    </div>
  )
}
