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
      <defs>
        <linearGradient id="tb-celeste" x1="50" y1="20" x2="50" y2="42" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#5EEAD4" />
          <stop offset="100%" stopColor="#00C2A8" />
        </linearGradient>
        <linearGradient id="tb-dark" x1="36" y1="43" x2="36" y2="65" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#2A5A8A" />
          <stop offset="100%" stopColor="#0F2D4A" />
        </linearGradient>
        <radialGradient id="tb-dotCeleste" cx="50%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#A7F3E8" />
          <stop offset="100%" stopColor="#00D4AA" />
        </radialGradient>
        <radialGradient id="tb-dotDark" cx="50%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#3A6EA5" />
          <stop offset="100%" stopColor="#0F2D4A" />
        </radialGradient>
      </defs>
      {/* Top hexagon — verde celeste */}
      <path
        d="M50 20.5 L59.2 25.9 L59.2 36.6 L50 42 L40.8 36.6 L40.8 25.9 Z"
        fill="none"
        stroke="url(#tb-celeste)"
        strokeWidth="2.4"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* Bottom-left — azul oscuro */}
      <path
        d="M36 43.2 L45.2 48.6 L45.2 59.3 L36 64.7 L26.8 59.3 L26.8 48.6 Z"
        fill="none"
        stroke="url(#tb-dark)"
        strokeWidth="2.4"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* Bottom-right — azul oscuro */}
      <path
        d="M64 43.2 L73.2 48.6 L73.2 59.3 L64 64.7 L54.8 59.3 L54.8 48.6 Z"
        fill="none"
        stroke="url(#tb-dark)"
        strokeWidth="2.4"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* Central connectors */}
      <g opacity="0.55">
        <line x1="50" y1="44.2" x2="46.5" y2="49.8" stroke="#3A6A8A" strokeWidth="0.6" />
        <line x1="50" y1="44.2" x2="53.5" y2="49.8" stroke="#3A6A8A" strokeWidth="0.6" />
        <line x1="45.2" y1="51.5" x2="54.8" y2="51.5" stroke="#3A6A8A" strokeWidth="0.6" />
      </g>
      {/* Three points — 1 verde celeste (top), 2 azul oscuro */}
      <circle cx="50" cy="41.5" r="4.2" fill="url(#tb-dotCeleste)" stroke="rgba(255,255,255,0.85)" strokeWidth="0.4" />
      <circle cx="43.8" cy="52.2" r="3.9" fill="url(#tb-dotDark)" stroke="rgba(255,255,255,0.18)" strokeWidth="0.4" />
      <circle cx="56.2" cy="52.2" r="3.9" fill="url(#tb-dotDark)" stroke="rgba(255,255,255,0.18)" strokeWidth="0.4" />
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
