import { BarChart3, FileUp, Home, PlusCircle, ReceiptText } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import clsx from 'clsx'

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/transactions', label: 'Transactions', icon: ReceiptText },
  { to: '/import', label: 'Import', icon: FileUp },
]

export function Sidebar() {
  return (
    <>
      <aside className="hidden w-64 border-r border-slate-200 bg-white p-4 md:flex md:flex-col">
        <div className="mb-6 flex items-center gap-2 px-2">
          <BarChart3 className="h-5 w-5 text-blue-600" />
          <span className="text-lg font-semibold">Business Dashboard</span>
        </div>
        <nav className="flex flex-col gap-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors',
                  isActive ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <NavLink to="/transactions/new" className="btn-primary mt-6 w-full gap-2">
          <PlusCircle className="h-4 w-4" />
          Add Transaction
        </NavLink>
      </aside>

      <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-slate-200 bg-white md:hidden">
        <div className="grid grid-cols-4">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex flex-col items-center gap-1 py-2 text-[11px] font-medium',
                  isActive ? 'text-blue-700' : 'text-slate-500',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
          <NavLink
            to="/transactions/new"
            className={({ isActive }) =>
              clsx(
                'flex flex-col items-center gap-1 py-2 text-[11px] font-medium',
                isActive ? 'text-blue-700' : 'text-slate-500',
              )
            }
          >
            <PlusCircle className="h-4 w-4" />
            Add
          </NavLink>
        </div>
      </nav>
    </>
  )
}
