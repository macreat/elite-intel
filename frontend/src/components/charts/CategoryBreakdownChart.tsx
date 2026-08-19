import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { CategoryBreakdown } from '../../types/dashboard'

const COLORS = ['#00d4aa', '#22d3ee', '#5eead4', '#06b6d4', '#2dd4bf', '#0891b2', '#14b8a6', '#67e8f9']

interface CategoryBreakdownChartProps {
  title: string
  data: CategoryBreakdown[]
}

export function CategoryBreakdownChart({ title, data }: CategoryBreakdownChartProps) {
  const numericData = data.map((entry): CategoryBreakdown => ({ ...entry, total: Number(entry.total) }))

  return (
    <div className="card h-80">
      <h3 className="mb-4 text-lg font-medium text-white">{title}</h3>
      <ResponsiveContainer width="100%" height="85%">
        <PieChart>
          <Pie
            data={numericData}
            dataKey="total"
            nameKey="category_name"
            cx="50%"
            cy="50%"
            outerRadius={95}
            innerRadius={50}
            strokeWidth={2}
            stroke="#0f1629"
          >
            {numericData.map((entry, index) => (
              <Cell key={`${entry.category_id}-${entry.category_name}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#151d35',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px',
              color: '#e2e8f0',
            }}
            formatter={(value: number, name: string) => [`${value.toLocaleString()} COP`, name]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
