import { clsx } from 'clsx'

interface KpiCardProps {
  title: string
  value: string
  tone?: 'neutral' | 'income' | 'expense'
}

const toneStyles: Record<NonNullable<KpiCardProps['tone']>, string> = {
  neutral: 'text-slate-900',
  income: 'text-emerald-600',
  expense: 'text-rose-600',
}

export function KpiCard({ title, value, tone = 'neutral' }: KpiCardProps) {
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{title}</p>
      <p className={clsx('mt-1 text-2xl font-semibold', toneStyles[tone])}>{value}</p>
    </div>
  )
}
