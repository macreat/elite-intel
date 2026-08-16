export type TransactionType = 'INCOME' | 'EXPENSE'
export type TransactionSourceType = 'MANUAL' | 'CSV' | 'EXCEL'

export interface Transaction {
  id: number
  occurred_at: string
  transaction_type: TransactionType
  category_id: number
  category_name?: string
  description: string
  amount: number
  currency_code: string
  product_id?: number | null
  notes?: string | null
  source_type: TransactionSourceType
  created_at: string
  updated_at: string
}

export interface TransactionPayload {
  occurred_at: string
  transaction_type: TransactionType
  category_id: number
  description: string
  amount: number
  product_id?: number | null
  notes?: string | null
}

export interface TransactionFilters {
  start_date?: string
  end_date?: string
  type?: TransactionType
  category_id?: number
  search?: string
  page?: number
  page_size?: number
}
