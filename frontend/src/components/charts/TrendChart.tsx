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
      <h3 className="mb-4 text-lg font-medium">Income / Expense Trend</h3>
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="income" name="Income" stroke="#059669" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="expenses" name="Expenses" stroke="#e11d48" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
