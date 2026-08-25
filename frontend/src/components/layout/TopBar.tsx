import { BookOpen, Home, PlusCircle, ReceiptText } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'
import clsx from 'clsx'

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/transactions', label: 'Transactions', icon: ReceiptText },
  { to: '/catalog', label: 'Catalog', icon: BookOpen },
]

function EliteLogo() {
  return (
    <svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Top — verde celeste */}
      <path d="M50 17 L61.5 23.6 L61.5 36.8 L50 43.4 L38.5 36.8 L38.5 23.6 Z" fill="none" stroke="#00D4AA" strokeWidth="2.6" strokeLinejoin="round" strokeLinecap="round" />
      {/* Bottom-left — azul oscuro */}
      <path d="M30 46.5 L41.5 53.1 L41.5 66.3 L30 72.9 L18.5 66.3 L18.5 53.1 Z" fill="none" stroke="#0F2D4A" strokeWidth="2.6" strokeLinejoin="round" strokeLinecap="round" />
      {/* Bottom-right — azul oscuro */}
      <path d="M70 46.5 L81.5 53.1 L81.5 66.3 L70 72.9 L58.5 66.3 L58.5 53.1 Z" fill="none" stroke="#0F2D4A" strokeWidth="2.6" strokeLinejoin="round" strokeLinecap="round" />
      {/* Connectors */}
      <g opacity="0.6">
        <line x1="50" y1="44" x2="44" y2="51.5" stroke="#2A4A6B" strokeWidth="0.6" />
        <line x1="50" y1="44" x2="56" y2="51.5" stroke="#2A4A6B" strokeWidth="0.6" />
        <line x1="45.2" y1="53.2" x2="54.8" y2="53.2" stroke="#2A4A6B" strokeWidth="0.6" />
      </g>
      {/* Three points */}
      <circle cx="50" cy="41.2" r="4.0" fill="#7EEAD4" stroke="white" strokeWidth="0.35" />
      <circle cx="42.8" cy="54.2" r="3.7" fill="#14365E" stroke="rgba(255,255,255,0.22)" strokeWidth="0.35" />
      <circle cx="57.2" cy="54.2" r="3.7" fill="#14365E" stroke="rgba(255,255,255,0.22)" strokeWidth="0.35" />
    </svg>
  )
}

export function TopBar() {
  return (
    <header className="border-b border-white/[0.06] bg-navy-800">
      {/* ELITE INTEL — centered, 3x big */}
      <Link
        to="/"
        className="flex items-center justify-center gap-3 py-6 transition-colors hover:bg-white/[0.03]"
      >
        <EliteLogo />
        <span className="text-5xl font-extrabold tracking-widest text-white">
          ELITE <span className="text-mint-500">INTEL</span>
        </span>
      </Link>

      {/* Floating bubble Add Transaction */}
      <div className="flex justify-center border-t border-white/[0.06] py-4">
        <NavLink
          to="/transactions/new"
          className="group relative"
        >
          <span
            className="absolute -inset-2 rounded-[28px_32px_26px_34px] bg-mint-500/20 blur-md transition-all group-hover:bg-mint-400/30 group-hover:blur-lg"
            style={{ borderRadius: '28px 32px 26px 34px' }}
          />
          <span
            className="relative flex items-center gap-2.5 rounded-[28px_32px_26px_34px] bg-gradient-to-r from-mint-600 to-mint-500 px-7 py-3 text-base font-bold text-white shadow-xl shadow-mint-600/30 transition-all duration-300 group-hover:scale-105 group-hover:shadow-mint-500/40"
            style={{ borderRadius: '28px 32px 26px 34px' }}
          >
            <PlusCircle className="h-5 w-5" />
            Add Transaction
          </span>
        </NavLink>
      </div>

      {/* Nav row — centered below button */}
      <div className="flex items-center justify-center gap-3 border-t border-white/[0.06] px-6 py-3">
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
      </div>
    </header>
  )
}
