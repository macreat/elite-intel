import type { Category } from '../../types/category'
import type { TransactionType } from '../../types/transaction'
import type { PeriodPreset } from '../../types/api'

interface TransactionFiltersProps {
  preset: PeriodPreset
  type?: TransactionType
  categoryId?: number
  search: string
  customStart?: string
  customEnd?: string
  categories: Category[]
  onPresetChange: (value: PeriodPreset) => void
  onTypeChange: (value?: TransactionType) => void
  onCategoryChange: (value?: number) => void
  onSearchChange: (value: string) => void
  onCustomStartChange: (value: string) => void
  onCustomEndChange: (value: string) => void
}

export function TransactionFilters({
  preset,
  type,
  categoryId,
  search,
  customStart,
  customEnd,
  categories,
  onPresetChange,
  onTypeChange,
  onCategoryChange,
  onSearchChange,
  onCustomStartChange,
  onCustomEndChange,
}: TransactionFiltersProps) {
  return (
    <div className="card grid gap-3 md:grid-cols-5">
      <div>
        <label className="label">Period</label>
        <select className="field" value={preset} onChange={(event) => onPresetChange(event.target.value as PeriodPreset)}>
          <option value="today">Today</option>
          <option value="week">Current Week</option>
          <option value="month">Current Month</option>
          <option value="previous_month">Previous Month</option>
          <option value="custom">Custom Range</option>
        </select>
      </div>

      <div>
        <label className="label">Type</label>
        <select
          className="field"
          value={type ?? ''}
          onChange={(event) => onTypeChange((event.target.value as TransactionType) || undefined)}
        >
          <option value="">All</option>
          <option value="INCOME">Income</option>
          <option value="EXPENSE">Expense</option>
        </select>
      </div>

      <div>
        <label className="label">Category</label>
        <select
          className="field"
          value={categoryId ?? ''}
          onChange={(event) => onCategoryChange(event.target.value ? Number(event.target.value) : undefined)}
        >
          <option value="">All</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </div>

      <div className="md:col-span-2">
        <label className="label">Search</label>
        <input
          className="field"
          placeholder="Description or notes"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
        />
      </div>

      {preset === 'custom' ? (
        <>
          <div>
            <label className="label">Start Date</label>
            <input className="field" type="date" value={customStart ?? ''} onChange={(event) => onCustomStartChange(event.target.value)} />
          </div>
          <div>
            <label className="label">End Date</label>
            <input className="field" type="date" value={customEnd ?? ''} onChange={(event) => onCustomEndChange(event.target.value)} />
          </div>
        </>
      ) : null}
    </div>
  )
}
