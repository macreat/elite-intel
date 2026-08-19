import { Outlet } from 'react-router-dom'
import { Sidebar } from '../components/layout/Sidebar'

export function RootLayout() {
  return (
    <div className="flex min-h-screen bg-navy-900">
      <Sidebar />
      <main className="w-full flex-1 p-4 pb-20 md:p-6 md:pb-6">
        <Outlet />
      </main>
    </div>
  )
}
