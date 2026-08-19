import { Outlet } from 'react-router-dom'
import { TopBar } from '../components/layout/TopBar'

export function RootLayout() {
  return (
    <div className="min-h-screen bg-navy-900">
      <TopBar />
      <main className="mx-auto w-full max-w-7xl p-4 pb-20 md:p-6">
        <Outlet />
      </main>
    </div>
  )
}
