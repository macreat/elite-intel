import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { CategoryBreakdown } from '../../types/dashboard'

const COLORS = ['#2563eb', '#0ea5e9', '#22c55e', '#eab308', '#f97316', '#ec4899', '#8b5cf6', '#14b8a6']

interface CategoryBreakdownChartProps {
  title: string
  data: CategoryBreakdown[]
}

export function CategoryBreakdownChart({ title, data }: CategoryBreakdownChartProps) {
  return (
    <div className="card h-80">
      <h3 className="mb-4 text-lg font-medium">{title}</h3>
      <ResponsiveContainer width="100%" height="85%">
        <PieChart>
          <Pie data={data} dataKey="total" nameKey="category_name" cx="50%" cy="50%" outerRadius={95} label>
            {data.map((entry, index) => (
              <Cell key={`${entry.category_id}-${entry.category_name}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
