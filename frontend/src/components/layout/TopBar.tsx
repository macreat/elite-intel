import { BookOpen, FileUp, Home, PlusCircle, ReceiptText } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'
import clsx from 'clsx'

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/transactions', label: 'Transactions', icon: ReceiptText },
  { to: '/import', label: 'Import', icon: FileUp },
  { to: '/catalog', label: 'Catalog', icon: BookOpen },
]

function EliteLogo() {
  return (
    <svg width="28" height="28" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M35 15 L60 5 L80 20 L80 45 L60 55 L35 45 Z" stroke="#00d4aa" strokeWidth="4" fill="none" />
      <path d="M55 45 L80 35 L100 50 L100 75 L80 85 L55 75 Z" stroke="#22d3ee" strokeWidth="4" fill="none" />
      <circle cx="52" cy="30" r="5" fill="#00d4aa" />
      <circle cx="60" cy="50" r="6" fill="#22d3ee" />
      <circle cx="48" cy="45" r="4" fill="#00d4aa" />
    </svg>
  )
}

export function TopBar() {
  return (
    <header className="sticky top-0 z-30 w-full border-b border-white/[0.06] bg-navy-800/95 backdrop-blur-md">
      <div className="relative mx-auto flex max-w-7xl flex-col items-center gap-3 px-4 py-3">
        <Link to="/" className="flex items-center gap-2 transition-opacity hover:opacity-80">
          <EliteLogo />
          <span className="text-lg font-bold text-white">ELITE</span>
          <span className="text-[10px] font-medium tracking-widest text-mint-500">INTEL</span>
        </Link>

        <nav className="flex items-center gap-1 rounded-full border border-white/10 bg-navy-700/60 p-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-2 rounded-full px-4 py-1.5 text-sm transition-all duration-200',
                  isActive
                    ? 'bg-mint-600/10 text-mint-500 shadow-sm shadow-mint-600/5'
                    : 'text-slate-400 hover:text-slate-200',
                )
              }
            >
              <Icon className="h-5 w-5" />
              {label}
            </NavLink>
          ))}
        </nav>

        <NavLink
          to="/transactions/new"
          className="btn-primary absolute right-4 top-1/2 -translate-y-1/2 gap-2"
        >
          <PlusCircle className="h-6 w-6" />
          <span className="hidden sm:inline">Add Transaction</span>
        </NavLink>
      </div>
    </header>
  )
}
