import { useEffect, useState } from 'react'
import { EmptyState, ErrorState, LoadingState } from '../components/common/States'
import { apiClient } from '../services/apiClient'
import { formatCurrency } from '../utils/format'
import type { PaginatedResponse } from '../types/api'
import type { CatalogItem } from '../types/catalog'
import { useAsyncData } from './hooks/useAsyncData'

export function CatalogPage() {
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)
  const page_size = 20

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  const state = useAsyncData<PaginatedResponse<CatalogItem>>(
    () => apiClient.listCatalog({ search: debouncedSearch || undefined, page, page_size }),
    [debouncedSearch, page],
  )

  const totalPages = Math.max(1, Math.ceil((state.data?.total ?? 0) / page_size))

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold text-white">Price Catalog</h1>
        <p className="text-sm text-slate-400">Searchable COP price dictionary of stationery products.</p>
      </header>

      <input
        type="text"
        className="field max-w-sm"
        placeholder="Search articles..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {state.loading ? <LoadingState message="Loading catalog..." /> : null}

      {!state.loading && state.error ? (
        <ErrorState
          title="Failed to load catalog"
          message={state.error}
          action={
            <button className="btn-secondary" onClick={() => setPage((p) => p)}>
              Retry
            </button>
          }
        />
      ) : null}

      {!state.loading && !state.error && state.data && state.data.total === 0 ? (
        <EmptyState title="No products found" message="Try a different search term." />
      ) : null}

      {!state.loading && !state.error && state.data && state.data.items.length > 0 ? (
        <>
          <div className="overflow-hidden rounded-xl border border-white/[0.06] bg-navy-700/60 backdrop-blur-sm">
            <table className="min-w-full divide-y divide-white/[0.06]">
              <thead className="bg-navy-800/50 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3">Articulo</th>
                  <th className="px-4 py-3">Valor Factura</th>
                  <th className="px-4 py-3">Valor /Local</th>
                  <th className="px-4 py-3">Stock</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {state.data.items.map((item) => (
                  <tr key={item.id} className="transition-colors hover:bg-white/[0.02]">
                    <td className="px-4 py-3 text-sm text-slate-200">{item.name}</td>
                    <td className="px-4 py-3 text-sm font-medium text-white">
                      {item.invoice_price != null ? formatCurrency(item.invoice_price, 'COP') : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-white">
                      {item.local_price != null ? formatCurrency(item.local_price, 'COP') : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-500">unknown</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <button
              className="btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <span className="text-sm text-slate-400">
              Page {page} of {totalPages}
            </span>
            <button
              className="btn-secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        </>
      ) : null}
    </div>
  )
}
