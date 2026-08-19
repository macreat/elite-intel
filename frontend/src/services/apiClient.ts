import axios from 'axios'
import type { Category } from '../types/category'
import type { CategoryBreakdown, DashboardSummary, TimeseriesPoint } from '../types/dashboard'
import type {
  ImportConfirmResponse,
  ImportMappingRequest,
  ImportMappingResponse,
  ImportUploadResponse,
} from '../types/import'
import type { PaginatedResponse } from '../types/api'
import type { CatalogItem } from '../types/catalog'
import type { Transaction, TransactionFilters, TransactionPayload } from '../types/transaction'

function resolveApiBaseUrl() {
  const runtimeBaseUrl = typeof window !== 'undefined' ? window.__ELITE_CONFIG__?.apiBaseUrl : undefined
  if (runtimeBaseUrl) return runtimeBaseUrl
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL
  return import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1'
}

const baseURL = resolveApiBaseUrl()

export const api = axios.create({
  baseURL,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.detail?.[0]?.msg ||
      error?.message ||
      'Unexpected error'
    return Promise.reject(new Error(message))
  },
)

function cleanParams<T extends object>(params: T): Partial<T> {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined)) as Partial<T>
}

function getBrowserTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
}

function withCalendarTimezone<T extends object>(params: T) {
  return cleanParams({ ...params, timezone: getBrowserTimezone() })
}

export const apiClient = {
  getDashboardSummary: async (params: { start_date: string; end_date: string }) => {
    const { data } = await api.get<DashboardSummary>('/dashboard/summary', { params: withCalendarTimezone(params) })
    return data
  },

  getDashboardCategories: async (params: { start_date: string; end_date: string; type?: 'INCOME' | 'EXPENSE' }) => {
    const { data } = await api.get<CategoryBreakdown[]>('/dashboard/categories', { params: withCalendarTimezone(params) })
    return data
  },

  getDashboardTimeseries: async (params: { start_date: string; end_date: string; granularity?: 'day' | 'week' | 'month' }) => {
    const { data } = await api.get<TimeseriesPoint[]>('/dashboard/timeseries', { params: withCalendarTimezone(params) })
    return data
  },

  listTransactions: async (filters: TransactionFilters) => {
    const { data } = await api.get<PaginatedResponse<Transaction>>('/transactions', {
      params: cleanParams({
        ...filters,
        timezone: getBrowserTimezone(),
      }),
    })
    return data
  },

  getTransaction: async (id: number) => {
    const { data } = await api.get<Transaction>(`/transactions/${id}`)
    return data
  },

  createTransaction: async (payload: TransactionPayload) => {
    const { data } = await api.post<Transaction>('/transactions', payload)
    return data
  },

  updateTransaction: async (id: number, payload: TransactionPayload) => {
    const { data } = await api.put<Transaction>(`/transactions/${id}`, payload)
    return data
  },

  deleteTransaction: async (id: number) => {
    await api.delete(`/transactions/${id}`)
  },

  listCategories: async (type?: 'INCOME' | 'EXPENSE') => {
    const { data } = await api.get<Category[]>('/categories', { params: cleanParams({ type, active: true }) })
    return data
  },

  uploadImportFile: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post<ImportUploadResponse>('/imports/transactions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return data
  },

  submitImportMapping: async (batchId: number, payload: ImportMappingRequest) => {
    const { data } = await api.post<ImportMappingResponse>(`/imports/${batchId}/mapping`, payload)
    return data
  },

  confirmImport: async (batchId: number) => {
    const { data } = await api.post<ImportConfirmResponse>(`/imports/${batchId}/confirm`)
    return data
  },

  listCatalog: async (params: { search?: string; page?: number; page_size?: number }) => {
    const { data } = await api.get<PaginatedResponse<CatalogItem>>('/catalog', { params: cleanParams(params) })
    return data
  },
}
