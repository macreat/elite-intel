import type { Category } from '../../types/category'
import type { TransactionPayload, TransactionType } from '../../types/transaction'
import { fromInputDate } from '../../utils/format'

export interface TransactionFormValues {
  occurred_at: string
  transaction_type: TransactionType
  category_id: string
  description: string
  amount: string
  notes: string
}

interface TransactionFormFieldsProps {
  values: TransactionFormValues
  categories: Category[]
  errors: Partial<Record<keyof TransactionFormValues, string>>
  loadingCategories?: boolean
  onChange: (name: keyof TransactionFormValues, value: string) => void
}

export function toPayload(values: TransactionFormValues): TransactionPayload {
  return {
    occurred_at: fromInputDate(values.occurred_at),
    transaction_type: values.transaction_type,
    category_id: Number(values.category_id),
    description: values.description.trim(),
    amount: Number(values.amount),
    notes: values.notes.trim() || null,
  }
}

export function TransactionFormFields({
  values,
  categories,
  errors,
  loadingCategories,
  onChange,
}: TransactionFormFieldsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="md:col-span-2">
        <span className="label">Type</span>
        <div className="flex gap-2">
          {(['INCOME', 'EXPENSE'] as const).map((type) => (
            <button
              key={type}
              type="button"
              className={
                values.transaction_type === type
                  ? 'btn-primary !rounded-full !px-4 !py-1.5'
                  : 'btn-secondary !rounded-full !px-4 !py-1.5'
              }
              onClick={() => onChange('transaction_type', type)}
            >
              {type === 'INCOME' ? 'Income' : 'Expense'}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="label" htmlFor="occurred_at">
          Date
        </label>
        <input
          id="occurred_at"
          className="field"
          type="date"
          value={values.occurred_at}
          onChange={(event) => onChange('occurred_at', event.target.value)}
        />
        {errors.occurred_at ? <p className="helper-error">{errors.occurred_at}</p> : null}
      </div>

      <div>
        <label className="label" htmlFor="category_id">
          Category
        </label>
        <select
          id="category_id"
          className="field"
          value={values.category_id}
          onChange={(event) => onChange('category_id', event.target.value)}
          disabled={loadingCategories}
        >
          <option value="">Select category</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
        {errors.category_id ? <p className="helper-error">{errors.category_id}</p> : null}
      </div>

      <div>
        <label className="label" htmlFor="amount">
          Amount
        </label>
        <input
          id="amount"
          className="field"
          type="number"
          min="0.01"
          step="0.01"
          value={values.amount}
          onChange={(event) => onChange('amount', event.target.value)}
          placeholder="0.00"
        />
        {errors.amount ? <p className="helper-error">{errors.amount}</p> : null}
      </div>

      <div>
        <label className="label" htmlFor="description">
          Description
        </label>
        <input
          id="description"
          className="field"
          value={values.description}
          onChange={(event) => onChange('description', event.target.value)}
          placeholder="Describe the transaction"
        />
        {errors.description ? <p className="helper-error">{errors.description}</p> : null}
      </div>

      <div className="md:col-span-2">
        <label className="label" htmlFor="notes">
          Notes (optional)
        </label>
        <textarea
          id="notes"
          className="field min-h-24"
          value={values.notes}
          onChange={(event) => onChange('notes', event.target.value)}
          placeholder="Additional context"
        />
      </div>
    </div>
  )
}
