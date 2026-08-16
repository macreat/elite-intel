import type { TransactionType } from './transaction'

export interface Category {
  id: number
  name: string
  type: TransactionType
  description?: string | null
  active: boolean
  created_at?: string
  updated_at?: string
}
