import { FileUp, Home, PlusCircle, ReceiptText } from 'lucide-react'
import { NavLink, Link } from 'react-router-dom'
import clsx from 'clsx'

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/transactions', label: 'Transactions', icon: ReceiptText },
  { to: '/import', label: 'Import', icon: FileUp },
]

function EliteLogo() {
  return (
    <svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M35 15 L60 5 L80 20 L80 45 L60 55 L35 45 Z" stroke="#00d4aa" strokeWidth="4" fill="none" />
      <path d="M55 45 L80 35 L100 50 L100 75 L80 85 L55 75 Z" stroke="#22d3ee" strokeWidth="4" fill="none" />
      <circle cx="52" cy="30" r="5" fill="#00d4aa" />
      <circle cx="60" cy="50" r="6" fill="#22d3ee" />
      <circle cx="48" cy="45" r="4" fill="#00d4aa" />
    </svg>
  )
}

export function Sidebar() {
  return (
    <>
      <aside className="hidden w-72 border-r border-white/[0.06] bg-navy-800 md:flex md:flex-col">
        {/* ELITE INTEL — full-width centered rectangle */}
        <Link
          to="/"
          className="flex flex-col items-center justify-center gap-3 border-b border-white/[0.06] px-6 py-10 transition-colors hover:bg-white/[0.03]"
        >
          <EliteLogo />
          <h1 className="text-center text-4xl font-extrabold tracking-widest text-white">
            ELITE <span className="text-mint-500">INTEL</span>
          </h1>
          <p className="text-xs tracking-wide text-slate-500">Business Dashboard</p>
        </Link>

        {/* Add Transaction — big prominent button */}
        <div className="px-5 pt-6 pb-2">
          <NavLink
            to="/transactions/new"
            className="flex items-center justify-center gap-2.5 rounded-xl bg-mint-600 px-5 py-3.5 text-base font-semibold text-white shadow-lg shadow-mint-600/20 transition-all hover:bg-mint-500 hover:shadow-mint-500/30"
          >
            <PlusCircle className="h-5 w-5" />
            Add Transaction
          </NavLink>
        </div>

        {/* Nav links centered */}
        <nav className="flex flex-1 flex-col items-center gap-1 px-5 pt-4">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-mint-600/10 text-mint-500 shadow-sm shadow-mint-600/5'
                    : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-white/[0.06] bg-navy-800/95 backdrop-blur-md md:hidden">
        <div className="grid grid-cols-4">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex flex-col items-center gap-1 py-2 text-[11px] font-medium',
                  isActive ? 'text-mint-500' : 'text-slate-500',
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
                isActive ? 'text-mint-500' : 'text-slate-500',
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
