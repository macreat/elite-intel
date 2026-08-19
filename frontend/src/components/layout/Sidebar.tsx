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
    <svg width="32" height="32" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
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
    <header className="flex items-center gap-6 border-b border-white/[0.06] bg-navy-800 px-6 py-3">
      {/* Logo + name — clickable */}
      <Link to="/" className="mr-4 flex items-center gap-2.5 shrink-0">
        <EliteLogo />
        <span className="text-xl font-extrabold tracking-widest text-white">
          ELITE <span className="text-mint-500">INTEL</span>
        </span>
      </Link>

      {/* Add Transaction */}
      <NavLink
        to="/transactions/new"
        className="mr-2 flex items-center gap-2 rounded-lg bg-mint-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-mint-600/20 transition-all hover:bg-mint-500"
      >
        <PlusCircle className="h-4 w-4" />
        Add Transaction
      </NavLink>

      {/* Nav links */}
      <nav className="flex items-center gap-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-mint-600/10 text-mint-500'
                  : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200',
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}
