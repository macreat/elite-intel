import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { EmptyState, ErrorState, LoadingState } from '../components/common/States'
import {
  TransactionFormFields,
  toPayload,
  type TransactionFormValues,
} from '../components/transactions/TransactionFormFields'
import { apiClient } from '../services/apiClient'
import type { Category } from '../types/category'
import { getTodayCalendarDate, toInputDate } from '../utils/format'
import { useAsyncData } from './hooks/useAsyncData'

const defaultValues: TransactionFormValues = {
  occurred_at: getTodayCalendarDate(),
  transaction_type: 'INCOME',
  category_id: '',
  description: '',
  amount: '',
  notes: '',
}

function validate(values: TransactionFormValues) {
  const errors: Partial<Record<keyof TransactionFormValues, string>> = {}
  if (!values.occurred_at) errors.occurred_at = 'Date is required'
  if (!values.category_id) errors.category_id = 'Category is required'
  if (!values.description.trim()) errors.description = 'Description is required'
  if (!values.amount || Number(values.amount) <= 0) errors.amount = 'Amount must be greater than 0'
  return errors
}

export function TransactionFormPage() {
  const params = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = Boolean(params.id)
  const transactionId = params.id ? Number(params.id) : null
  const [values, setValues] = useState<TransactionFormValues>(defaultValues)
  const [errors, setErrors] = useState<Partial<Record<keyof TransactionFormValues, string>>>({})
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const existingState = useAsyncData(
    async () => {
      if (!isEdit || !transactionId) {
        return null
      }
      return apiClient.getTransaction(transactionId)
    },
    [isEdit, transactionId],
  )

  const categoriesState = useAsyncData<Category[]>(
    () => apiClient.listCategories(values.transaction_type),
    [values.transaction_type],
  )

  useMemo(() => {
    if (!existingState.data) return
    setValues({
      occurred_at: toInputDate(existingState.data.occurred_at),
      transaction_type: existingState.data.transaction_type,
      category_id: String(existingState.data.category_id),
      description: existingState.data.description,
      amount: String(existingState.data.amount),
      notes: existingState.data.notes ?? '',
    })
  }, [existingState.data])

  const handleChange = (name: keyof TransactionFormValues, value: string) => {
    setValues((prev) => {
      const next = { ...prev, [name]: value }
      if (name === 'transaction_type') {
        next.category_id = ''
      }
      return next
    })
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const validation = validate(values)
    setErrors(validation)
    setSaveError(null)
    if (Object.keys(validation).length > 0) return

    setSaving(true)
    try {
      const payload = toPayload(values)
      if (isEdit && transactionId) {
        await apiClient.updateTransaction(transactionId, payload)
      } else {
        await apiClient.createTransaction(payload)
      }
      navigate('/transactions')
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save transaction')
    } finally {
      setSaving(false)
    }
  }

  if (isEdit && existingState.loading) {
    return <LoadingState message="Loading transaction..." />
  }

  if (isEdit && existingState.error) {
    return <ErrorState title="Failed to load transaction" message={existingState.error} />
  }

  if (isEdit && !existingState.data) {
    return <EmptyState title="Transaction not found" message="The requested transaction was not found." />
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{isEdit ? 'Edit Transaction' : 'Add Transaction'}</h1>
          <p className="text-sm text-slate-500">Register income or expense transactions quickly.</p>
        </div>
        <Link to="/transactions" className="btn-secondary">
          Back
        </Link>
      </header>

      <form className="card" onSubmit={handleSubmit}>
        <TransactionFormFields
          values={values}
          categories={categoriesState.data ?? []}
          errors={errors}
          loadingCategories={categoriesState.loading}
          onChange={handleChange}
        />

        {saveError ? <p className="helper-error mt-4">{saveError}</p> : null}

        <div className="mt-6 flex justify-end gap-2">
          <Link to="/transactions" className="btn-secondary">
            Cancel
          </Link>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  )
}
