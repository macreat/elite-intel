import { clsx } from 'clsx'

interface KpiCardProps {
  title: string
  value: string
  tone?: 'neutral' | 'income' | 'expense'
}

const toneStyles: Record<NonNullable<KpiCardProps['tone']>, string> = {
  neutral: 'text-white',
  income: 'text-mint-500',
  expense: 'text-rose-400',
}

const toneAccent: Record<NonNullable<KpiCardProps['tone']>, string> = {
  neutral: 'from-cyan-500/10 to-transparent',
  income: 'from-mint-600/10 to-transparent',
  expense: 'from-rose-500/10 to-transparent',
}

export function KpiCard({ title, value, tone = 'neutral' }: KpiCardProps) {
  return (
    <div className="card relative overflow-hidden">
      <div className={clsx('absolute inset-0 bg-gradient-to-br opacity-60', toneAccent[tone])} />
      <div className="relative">
        <p className="text-sm text-slate-400">{title}</p>
        <p className={clsx('mt-1 text-2xl font-semibold', toneStyles[tone])}>{value}</p>
      </div>
    </div>
  )
}
