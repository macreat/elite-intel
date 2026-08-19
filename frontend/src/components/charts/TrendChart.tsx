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
            domain={[0, 10000000]}
            allowDataOverflow
            ticks={[0, 1000000, 2000000, 3000000, 4000000, 5000000, 6000000, 7000000, 8000000, 9000000, 10000000]}
            tickFormatter={(v: number) => {
              if (v === 0) return '0'
              if (v >= 1_000_000) return `${v / 1_000_000}M`
              return `${v / 1_000}K`
            }}
            width={55}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#151d35',
              border: '1px solid rgba(255,255,255,0.15)',
              borderRadius: '12px',
              color: '#ffffff',
              fontSize: '14px',
              fontWeight: 600,
              padding: '10px 14px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            }}
            itemStyle={{ color: '#ffffff', fontSize: '14px' }}
            labelStyle={{ color: '#ffffff', fontSize: '15px', fontWeight: 700, marginBottom: '4px' }}
            formatter={(value: number) => [`${Number(value).toLocaleString()} COP`]}
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
