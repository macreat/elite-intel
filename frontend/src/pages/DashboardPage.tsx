import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { PeriodFilter } from '../components/filters/PeriodFilter'
import { CategoryBreakdownChart } from '../components/charts/CategoryBreakdownChart'
import { TrendChart } from '../components/charts/TrendChart'
import { KpiCard } from '../components/kpi/KpiCard'
import { EmptyState, ErrorState, LoadingState } from '../components/common/States'
import { usePeriod } from '../hooks/usePeriod'
import { apiClient } from '../services/apiClient'
import { formatCurrency, formatDate, formatPercent } from '../utils/format'
import type { DashboardSummary, CategoryBreakdown, TimeseriesPoint } from '../types/dashboard'
import type { Transaction } from '../types/transaction'
import { useAsyncData } from './hooks/useAsyncData'

export function DashboardPage() {
  const period = usePeriod('month')

  const summaryState = useAsyncData<DashboardSummary>(
    () => apiClient.getDashboardSummary(period.range),
    [period.range.start_date, period.range.end_date],
  )

  const timeseriesState = useAsyncData<TimeseriesPoint[]>(
    () => apiClient.getDashboardTimeseries(period.range),
    [period.range.start_date, period.range.end_date],
  )

  const incomeCategoriesState = useAsyncData<CategoryBreakdown[]>(
    () => apiClient.getDashboardCategories({ ...period.range, type: 'INCOME' }),
    [period.range.start_date, period.range.end_date, 'income'],
  )

  const expenseCategoriesState = useAsyncData<CategoryBreakdown[]>(
    () => apiClient.getDashboardCategories({ ...period.range, type: 'EXPENSE' }),
    [period.range.start_date, period.range.end_date, 'expense'],
  )

  const recentTransactionsState = useAsyncData<{ items: Transaction[] }>(
    async () => {
      const data = await apiClient.listTransactions({
        ...period.range,
        page: 1,
        page_size: 10,
      })
      return { items: data.items }
    },
    [period.range.start_date, period.range.end_date],
  )

  const isLoading =
    summaryState.loading ||
    timeseriesState.loading ||
    incomeCategoriesState.loading ||
    expenseCategoriesState.loading ||
    recentTransactionsState.loading

  const error =
    summaryState.error ||
    timeseriesState.error ||
    incomeCategoriesState.error ||
    expenseCategoriesState.error ||
    recentTransactionsState.error

  const hasData = useMemo(() => {
    return (summaryState.data?.transaction_count ?? 0) > 0
  }, [summaryState.data])

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-2xl font-semibold">Business Dashboard</h1>
          <p className="text-sm text-slate-500">Track income, expenses, and savings performance.</p>
        </div>
        <PeriodFilter
          preset={period.preset}
          customStart={period.customStart}
          customEnd={period.customEnd}
          onPresetChange={period.setPreset}
          onCustomStartChange={period.setCustomStart}
          onCustomEndChange={period.setCustomEnd}
        />
      </header>

      {isLoading ? <LoadingState message="Loading dashboard data..." /> : null}

      {!isLoading && error ? (
        <ErrorState
          title="Failed to load dashboard data"
          message={error}
          action={
            <button type="button" className="btn-secondary" onClick={() => window.location.reload()}>
              Retry
            </button>
          }
        />
      ) : null}

      {!isLoading && !error && !hasData ? (
        <EmptyState
          title="No transactions found for this period"
          message="Add a transaction to see your metrics."
          action={
            <Link to="/transactions/new" className="btn-primary">
              Add Transaction
            </Link>
          }
        />
      ) : null}

      {!isLoading && !error && hasData && summaryState.data ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <KpiCard title="Income" value={formatCurrency(summaryState.data.total_income)} tone="income" />
            <KpiCard title="Expenses" value={formatCurrency(summaryState.data.total_expenses)} tone="expense" />
            <KpiCard title="Net Balance" value={formatCurrency(summaryState.data.net_balance)} />
            <KpiCard title="Estimated Savings" value={formatCurrency(summaryState.data.estimated_savings)} />
            <KpiCard title="Savings Rate" value={formatPercent(summaryState.data.savings_rate)} />
            <KpiCard title="Transaction Count" value={String(summaryState.data.transaction_count)} />
          </section>

          <TrendChart data={timeseriesState.data ?? []} />

          <section className="grid gap-4 lg:grid-cols-2">
            <CategoryBreakdownChart title="Income by Category" data={incomeCategoriesState.data ?? []} />
            <CategoryBreakdownChart title="Expenses by Category" data={expenseCategoriesState.data ?? []} />
          </section>

          <section className="card">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-medium">Recent Transactions</h2>
              <Link to="/transactions" className="text-sm font-medium text-blue-600 hover:text-blue-700">
                View all
              </Link>
            </div>
            <div className="grid gap-3">
              {(recentTransactionsState.data?.items ?? []).slice(0, 10).map((transaction) => (
                <div key={transaction.id} className="grid grid-cols-[100px_90px_1fr_auto] items-center gap-2 text-sm">
                  <span className="text-slate-500">{formatDate(transaction.occurred_at)}</span>
                  <span className="text-xs font-medium text-slate-700">{transaction.transaction_type}</span>
                  <span className="truncate">{transaction.description}</span>
                  <span className="font-medium">{formatCurrency(transaction.amount, transaction.currency_code)}</span>
                </div>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </div>
  )
}
