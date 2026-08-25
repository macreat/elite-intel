import { useEffect, useMemo, useRef, useState } from 'react'
import { EmptyState, ErrorState, LoadingState } from '../common/States'
import { apiClient } from '../../services/apiClient'
import type { CatalogItem, StockBulkEntry } from '../../types/catalog'

interface StockBulkModalProps {
  open: boolean
  onClose: () => void
  onApplied: () => void
}

export function StockBulkModal({ open, onClose, onApplied }: StockBulkModalProps) {
  const [products, setProducts] = useState<CatalogItem[]>([])
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [inputs, setInputs] = useState<Record<number, string>>({})
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const requestSeq = useRef(0)

  useEffect(() => {
    if (!open) return
    const seq = ++requestSeq.current
    setLoading(true)
    setLoadError(null)
    setSaveError(null)
    setSearch('')
    setInputs({})
    apiClient
      .listAllCatalogProducts()
      .then((items) => {
        if (seq !== requestSeq.current) return
        setProducts(items)
      })
      .catch((err: Error) => {
        if (seq !== requestSeq.current) return
        setLoadError(err.message)
      })
      .finally(() => {
        if (seq !== requestSeq.current) return
        setLoading(false)
      })
  }, [open])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return products
    return products.filter((p) => p.name.toLowerCase().includes(term))
  }, [products, search])

  const changedEntries: StockBulkEntry[] = useMemo(() => {
    const entries: StockBulkEntry[] = []
    for (const product of products) {
      const raw = inputs[product.id]
      if (raw === undefined || raw.trim() === '') continue
      entries.push({ product_id: product.id, stock: Number(raw.trim()) })
    }
    return entries
  }, [products, inputs])

  const invalidInput = Object.entries(inputs).some(([, raw]) => {
    const text = raw.trim()
    if (text === '') return false
    return !/^\d+$/.test(text)
  })

  const handleApply = async () => {
    if (invalidInput || changedEntries.length === 0) return
    setSaving(true)
    setSaveError(null)
    try {
      await apiClient.bulkUpdateStock({ items: changedEntries })
      onApplied()
      onClose()
    } catch (err) {
      setSaveError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="flex max-h-[55vh] w-full max-w-md flex-col rounded-xl border border-white/[0.06] bg-navy-700 p-4 shadow-xl">
        <h3 className="text-lg font-semibold text-white">Change stock</h3>
        <p className="mt-1 text-sm text-slate-400">
          Set the stock for each article. Empty means leave it unchanged. Applies to every edited article in a single save.
        </p>

        {loading ? <LoadingState message="Loading catalog..." /> : null}
        {!loading && loadError ? (
          <ErrorState title="Failed to load products" message={loadError} />
        ) : null}

        {!loading && !loadError ? (
          <>
            <input
              type="text"
              className="field mt-4"
              placeholder="Filter articles..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <div className="mt-3 min-h-0 flex-1 overflow-y-auto rounded-lg border border-white/[0.06]">
              {filtered.length === 0 ? (
                <EmptyState title="No products found" message="Try a different filter." />
              ) : (
                <table className="min-w-full divide-y divide-white/[0.06]">
                  <thead className="sticky top-0 bg-navy-800 text-left text-xs uppercase tracking-wide text-slate-400">
                    <tr>
                      <th className="px-3 py-2">Articulo</th>
                      <th className="px-3 py-2 w-24">Current</th>
                      <th className="px-3 py-2 w-32">New stock</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {filtered.map((product) => {
                      const value = inputs[product.id]
                      return (
                        <tr key={product.id}>
                          <td className="px-3 py-2 text-sm text-slate-200">{product.name}</td>
                          <td className="px-3 py-2 text-sm text-slate-400">
                            {product.stock_qty ?? '—'}
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="number"
                              min={0}
                              step={1}
                              className="field py-1 text-sm"
                              aria-label={`New stock for ${product.name}`}
                              value={value ?? ''}
                              onChange={(e) =>
                                setInputs((prev) => ({ ...prev, [product.id]: e.target.value }))
                              }
                            />
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>

            {invalidInput ? (
              <p className="mt-2 text-sm text-rose-400">Stock must be a whole number greater than or equal to 0.</p>
            ) : null}
            {saveError ? <p className="mt-2 text-sm text-rose-400">{saveError}</p> : null}

            <div className="mt-5 flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={onClose} disabled={saving}>
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={handleApply}
                disabled={saving || invalidInput || changedEntries.length === 0}
              >
                {saving ? 'Applying...' : `Apply${changedEntries.length > 0 ? ` (${changedEntries.length})` : ''}`}
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
