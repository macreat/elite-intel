export interface DashboardSummary {
  total_income: number
  total_expenses: number
  net_balance: number
  estimated_savings: number
  savings_rate: number
  transaction_count: number
  period: {
    start_date: string
    end_date: string
  }
}

export interface CategoryBreakdown {
  category_id: number
  category_name: string
  total: number
  percentage: number
}

export interface TimeseriesPoint {
  date: string
  income: number
  expenses: number
}
