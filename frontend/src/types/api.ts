export type PeriodPreset = 'today' | 'week' | 'month' | 'previous_month' | 'year' | 'all_time' | 'custom'

export interface CalendarDateRange {
  start_date: string
  end_date: string
}

export interface ApiError {
  message: string
  code?: string
  details?: unknown
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
