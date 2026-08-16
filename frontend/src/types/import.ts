export interface ImportUploadResponse {
  batch_id: number
  status: 'PENDING'
  columns_detected: string[]
  suggested_mapping: Record<string, string>
}

export interface ImportMappingRequest {
  mapping: Record<string, string>
}

export interface InvalidRow {
  row_number: number
  error_code: string
  message: string
}

export interface ImportMappingResponse {
  batch_id: number
  status: 'VALIDATED'
  summary: {
    records_total: number
    records_valid: number
    records_invalid: number
    records_duplicate: number
  }
  preview: Array<{
    occurred_at: string
    transaction_type: 'INCOME' | 'EXPENSE'
    category_id: number
    description: string
    amount: number
    notes?: string | null
  }>
  invalid_rows: InvalidRow[]
}

export interface ImportConfirmResponse {
  batch_id: number
  status: 'CONFIRMED'
  records_inserted: number
}
