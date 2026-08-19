export interface CatalogItem {
  id: number
  name: string
  category_id: number
  description: string | null
  active: boolean
  invoice_price: number | null
  local_price: number | null
  currency_code: string
  stock_qty: number | null
  created_at: string
  updated_at: string
}
