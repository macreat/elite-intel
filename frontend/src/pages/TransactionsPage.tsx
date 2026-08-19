import { useMemo, useState } from 'react'
import { DeleteConfirmModal } from '../components/transactions/DeleteConfirmModal'
import { TransactionTable } from '../components/transactions/TransactionTable'
import { TransactionFilters } from '../components/filters/TransactionFilters'
import { EmptyState, ErrorState, LoadingState } from '../components/common/States'
import { usePeriod } from '../hooks/usePeriod'
import { apiClient } from '../services/apiClient'
import type { Category } from '../types/category'
import type { Transaction, TransactionType } from '../types/transaction'
import { useAsyncData } from './hooks/useAsyncData'

export function TransactionsPage() {
  const period = usePeriod('month')
  const [typeFilter, setTypeFilter] = useState<TransactionType | undefined>()
  const [categoryFilter, setCategoryFilter] = useState<number | undefined>()
  const [search, setSearch] = useState('')
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  const categoriesState = useAsyncData<Category[]>(
    () => apiClient.listCategories(typeFilter),
    [typeFilter],
  )

  const transactionsState = useAsyncData<{ items: Transaction[]; total: number }>(
    async () => {
      const response = await apiClient.listTransactions({
        ...period.range,
        type: typeFilter,
        category_id: categoryFilter,
        search: search || undefined,
        page: 1,
        page_size: 200,
      })
      return { items: response.items, total: response.total }
    },
    [period.range.start_date, period.range.end_date, typeFilter, categoryFilter, search, reloadKey],
  )

  const isLoading = categoriesState.loading || transactionsState.loading
  const error = categoriesState.error || transactionsState.error

  const hasRows = useMemo(() => (transactionsState.data?.items.length ?? 0) > 0, [transactionsState.data?.items.length])

  const handleDelete = async () => {
    if (!deleteId) return

    setDeleteLoading(true)
    try {
      await apiClient.deleteTransaction(deleteId)
      setDeleteId(null)
      setReloadKey((prev) => prev + 1)
    } catch {
      setDeleteId(null)
    } finally {
      setDeleteLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold text-white">Transaction History</h1>
        <p className="text-sm text-slate-400">Filter, search, edit, and delete your transactions.</p>
      </header>

      <TransactionFilters
        preset={period.preset}
        type={typeFilter}
        categoryId={categoryFilter}
        search={search}
        customStart={period.customStart}
        customEnd={period.customEnd}
        categories={categoriesState.data ?? []}
        onPresetChange={period.setPreset}
        onTypeChange={setTypeFilter}
        onCategoryChange={setCategoryFilter}
        onSearchChange={setSearch}
        onCustomStartChange={period.setCustomStart}
        onCustomEndChange={period.setCustomEnd}
      />

      {isLoading ? <LoadingState message="Loading transactions..." /> : null}

      {!isLoading && error ? (
        <ErrorState title="Failed to load transactions" message={error} action={<button className="btn-secondary" onClick={() => setReloadKey((v) => v + 1)}>Retry</button>} />
      ) : null}

      {!isLoading && !error && !hasRows ? (
        <EmptyState title="No transactions found" message="Try another filter or create a new transaction." />
      ) : null}

      {!isLoading && !error && hasRows ? (
        <TransactionTable items={transactionsState.data?.items ?? []} onDelete={setDeleteId} />
      ) : null}

      <DeleteConfirmModal
        open={deleteId !== null}
        loading={deleteLoading}
        onCancel={() => setDeleteId(null)}
        onConfirm={handleDelete}
      />
    </div>
  )
}
