import { useEffect, useMemo, useRef, useState } from 'react'
import { EmptyState, ErrorState, LoadingState } from '../common/States'
import { apiClient } from '../../services/apiClient'
import type { CatalogItem, PriceBulkEntry } from '../../types/catalog'

interface InventoryModalProps {
  open: boolean
  onClose: () => void
  onApplied: () => void
  initialTab?: Tab
}

type Tab = 'add' | 'prices'

const NUMERIC_PATTERN = /^\d+(\.\d+)?$/
const WHOLE_PATTERN = /^\d+$/

function parseOptionalNumber(raw: string | undefined): number | null {
  const text = raw?.trim() ?? ''
  if (text === '') return null
  return Number(text)
}

export function InventoryModal({ open, onClose, onApplied, initialTab }: InventoryModalProps) {
  const [tab, setTab] = useState<Tab>(initialTab ?? 'add')

  useEffect(() => {
    if (open) setTab(initialTab ?? 'add')
  }, [open, initialTab])

  useEffect(() => {
    if (!open) return
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  if (!open) return null

  const singleMode = initialTab !== undefined
  const title = initialTab === 'prices' ? 'Update prices' : initialTab === 'add' ? 'Add product' : 'Update inventory'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={onClose}>
      <div
        className="flex max-h-[24vh] w-[clamp(220px,18vw,12rem)] flex-col rounded-xl border border-white/[0.06] bg-navy-700 p-1.5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-xs font-semibold text-white">{title}</h3>
          <button type="button" onClick={onClose} className="rounded p-1 text-slate-400 hover:text-white" aria-label="Close">
            ✕
          </button>
        </div>

        {!singleMode ? (
          <div className="mt-2 flex gap-1 rounded-lg border border-white/[0.06] bg-navy-800/60 p-1">
            <button
              type="button"
              className={`flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${
                tab === 'add' ? 'bg-navy-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
              onClick={() => setTab('add')}
            >
              Add product
            </button>
            <button
              type="button"
              className={`flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${
                tab === 'prices' ? 'bg-navy-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
              onClick={() => setTab('prices')}
            >
              Update prices
            </button>
          </div>
        ) : null}

        <div className="mt-2 min-h-0 flex-1 overflow-y-auto">
          {(singleMode ? initialTab : tab) === 'add' ? (
            <AddProductForm onCreated={onApplied} onClose={onClose} />
          ) : (
            <UpdatePricesPanel onApplied={onApplied} onClose={onClose} />
          )}
        </div>
      </div>
    </div>
  )
}

interface AddProductFormProps {
  onCreated: () => void
  onClose: () => void
}

function AddProductForm({ onCreated, onClose }: AddProductFormProps) {
  const [name, setName] = useState('')
  const [invoicePrice, setInvoicePrice] = useState('')
  const [localPrice, setLocalPrice] = useState('')
  const [stockQty, setStockQty] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const invalid =
    !name.trim() ||
    [invoicePrice, localPrice].some((raw) => {
      const text = raw.trim()
      if (text === '') return false
      return !NUMERIC_PATTERN.test(text)
    }) ||
    (stockQty.trim() !== '' && !WHOLE_PATTERN.test(stockQty.trim()))

  const handleCreate = async () => {
    if (invalid || saving) return
    setSaving(true)
    setSaveError(null)
    try {
      await apiClient.createProduct({
        name: name.trim(),
        invoice_price: parseOptionalNumber(invoicePrice) ?? undefined,
        local_price: parseOptionalNumber(localPrice) ?? undefined,
        stock_qty: parseOptionalNumber(stockQty) ?? undefined,
      })
      onCreated()
      onClose()
    } catch (err) {
      setSaveError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="flex flex-col gap-2 p-1"
      onSubmit={(e) => {
        e.preventDefault()
        void handleCreate()
      }}
    >
      <label className="flex flex-col gap-1">
        <span className="text-[10px] uppercase tracking-wide text-slate-400">Articulo</span>
        <input
          type="text"
          className="field py-1 text-xs"
          placeholder="Product name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </label>

      <div className="grid grid-cols-3 gap-2">
        <label className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wide text-slate-400">Valor Factura</span>
          <input
            type="number"
            min={0}
            step="any"
            className="field py-1 text-xs"
            aria-label="Invoice price"
            value={invoicePrice}
            onChange={(e) => setInvoicePrice(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wide text-slate-400">Valor Local</span>
          <input
            type="number"
            min={0}
            step="any"
            className="field py-1 text-xs"
            aria-label="Local price"
            value={localPrice}
            onChange={(e) => setLocalPrice(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wide text-slate-400">Stock</span>
          <input
            type="number"
            min={0}
            step={1}
            className="field py-1 text-xs"
            aria-label="Initial stock"
            value={stockQty}
            onChange={(e) => setStockQty(e.target.value)}
          />
        </label>
      </div>

      {invalid && name.trim() !== '' ? (
        <p className="text-[11px] text-rose-400">Prices must be numbers ≥ 0 and stock a whole number ≥ 0.</p>
      ) : null}
      {saveError ? <p className="text-[11px] text-rose-400">{saveError}</p> : null}

      <div className="mt-1 flex justify-end gap-2">
        <button type="button" className="btn-secondary px-3 py-1 text-xs" onClick={onClose} disabled={saving}>
          Cancel
        </button>
        <button type="submit" className="btn-primary px-3 py-1 text-xs" disabled={invalid || saving}>
          {saving ? 'Adding...' : 'Add product'}
        </button>
      </div>
    </form>
  )
}

function UpdatePricesPanel({ onApplied, onClose }: { onApplied: () => void; onClose: () => void }) {
  const [products, setProducts] = useState<CatalogItem[]>([])
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [invoiceInputs, setInvoiceInputs] = useState<Record<number, string>>({})
  const [localInputs, setLocalInputs] = useState<Record<number, string>>({})
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const requestSeq = useRef(0)

  useEffect(() => {
    const seq = ++requestSeq.current
    setLoading(true)
    setLoadError(null)
    setSaveError(null)
    setSearch('')
    setInvoiceInputs({})
    setLocalInputs({})
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
  }, [])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return products
    return products.filter((p) => p.name.toLowerCase().includes(term))
  }, [products, search])

  const invalidInput = [...Object.values(invoiceInputs), ...Object.values(localInputs)].some((raw) => {
    const text = raw.trim()
    if (text === '') return false
    return !NUMERIC_PATTERN.test(text)
  })

  const changedEntries: PriceBulkEntry[] = useMemo(() => {
    const entries: PriceBulkEntry[] = []
    for (const product of products) {
      const invoice = parseOptionalNumber(invoiceInputs[product.id])
      const local = parseOptionalNumber(localInputs[product.id])
      if (invoice === null && local === null) continue
      const entry: PriceBulkEntry = { product_id: product.id }
      if (invoice !== null) entry.invoice_price = invoice
      if (local !== null) entry.local_price = local
      entries.push(entry)
    }
    return entries
  }, [products, invoiceInputs, localInputs])

  const handleApply = async () => {
    if (invalidInput || changedEntries.length === 0) return
    setSaving(true)
    setSaveError(null)
    try {
      const result = await apiClient.bulkUpdatePrices({ items: changedEntries })
      const updatedById = new Map(result.items.map((item) => [item.id, item]))
      setProducts((prev) => prev.map((p) => updatedById.get(p.id) ?? p))
      setInvoiceInputs({})
      setLocalInputs({})
      onApplied()
    } catch (err) {
      setSaveError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingState message="Loading catalog..." />

  if (loadError) return <ErrorState title="Failed to load products" message={loadError} />

  return (
    <div className="flex min-h-0 flex-col">
      <input
        type="text"
        className="field py-1 text-xs"
        placeholder="Filter articles..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="mt-2 min-h-0 flex-1 overflow-y-auto rounded-lg border border-white/[0.06]">
        {filtered.length === 0 ? (
          <EmptyState title="No products found" message="Try a different filter." />
        ) : (
          <table className="min-w-full divide-y divide-white/[0.06]">
            <thead className="sticky top-0 bg-navy-800 text-left text-[10px] uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-2 py-1">Articulo</th>
                <th className="px-2 py-1 w-16">Factura</th>
                <th className="px-2 py-1 w-16">Local</th>
                <th className="px-2 py-1 w-20">New Invoice</th>
                <th className="px-2 py-1 w-20">New Local</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {filtered.map((product) => (
                <tr key={product.id}>
                  <td className="px-2 py-1 text-xs text-slate-200">{product.name}</td>
                  <td className="px-2 py-1 text-xs text-slate-400">{product.invoice_price ?? '—'}</td>
                  <td className="px-2 py-1 text-xs text-slate-400">{product.local_price ?? '—'}</td>
                  <td className="px-2 py-1">
                    <input
                      type="number"
                      min={0}
                      step="any"
                      className="field px-1 py-0.5 text-xs"
                      aria-label={`New invoice price for ${product.name}`}
                      placeholder="(unchanged)"
                      value={invoiceInputs[product.id] ?? ''}
                      onChange={(e) =>
                        setInvoiceInputs((prev) => ({ ...prev, [product.id]: e.target.value }))
                      }
                    />
                  </td>
                  <td className="px-2 py-1">
                    <input
                      type="number"
                      min={0}
                      step="any"
                      className="field px-1 py-0.5 text-xs"
                      aria-label={`New local price for ${product.name}`}
                      placeholder="(unchanged)"
                      value={localInputs[product.id] ?? ''}
                      onChange={(e) =>
                        setLocalInputs((prev) => ({ ...prev, [product.id]: e.target.value }))
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {invalidInput ? (
        <p className="mt-1 text-[11px] text-rose-400">Prices must be numbers ≥ 0.</p>
      ) : null}
      {saveError ? <p className="mt-1 text-[11px] text-rose-400">{saveError}</p> : null}

      <div className="mt-3 flex justify-end gap-2">
        <button type="button" className="btn-secondary px-3 py-1 text-xs" onClick={onClose} disabled={saving}>
          Cancel
        </button>
        <button
          type="button"
          className="btn-primary px-3 py-1 text-xs"
          onClick={() => void handleApply()}
          disabled={saving || invalidInput || changedEntries.length === 0}
        >
          {saving ? 'Applying...' : `Apply${changedEntries.length > 0 ? ` (${changedEntries.length})` : ''}`}
        </button>
      </div>
    </div>
  )
}
