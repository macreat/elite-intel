import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TimeseriesPoint } from '../../types/dashboard'

interface TrendChartProps {
  data: TimeseriesPoint[]
}

export function TrendChart({ data }: TrendChartProps) {
  return (
    <div className="card h-80">
      <h3 className="mb-4 text-lg font-medium text-white">Income / Expense Trend</h3>
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <YAxis
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            domain={[0, 400_000_000]}
            tickFormatter={(v: number) => {
              if (v === 0) return '0'
              if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(1)}B`
              if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(0)}M`
              if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`
              return String(v)
            }}
            width={65}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#151d35',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px',
              color: '#e2e8f0',
            }}
          />
          <Legend wrapperStyle={{ color: '#94a3b8' }} />
          <Line
            type="monotone"
            dataKey="income"
            name="Income"
            stroke="#00d4aa"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 5, fill: '#00d4aa', stroke: '#0f1629', strokeWidth: 2 }}
          />
          <Line
            type="monotone"
            dataKey="expenses"
            name="Expenses"
            stroke="#f43f5e"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 5, fill: '#f43f5e', stroke: '#0f1629', strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
