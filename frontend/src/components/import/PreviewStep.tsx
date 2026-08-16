import { formatCurrency, formatDate } from '../../utils/format'
import type { ImportMappingResponse } from '../../types/import'

interface PreviewStepProps {
  data: ImportMappingResponse
  loading: boolean
  onConfirm: () => void
}

export function PreviewStep({ data, loading, onConfirm }: PreviewStepProps) {
  return (
    <section className="card">
      <h2 className="text-lg font-medium">4) Preview and confirm</h2>
      <p className="mt-1 text-sm text-slate-500">Showing up to first 10 valid records.</p>

      <div className="mt-4 overflow-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-100 text-left text-xs uppercase text-slate-600">
            <tr>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Category ID</th>
              <th className="px-3 py-2">Description</th>
              <th className="px-3 py-2">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.preview.map((row, index) => (
              <tr key={`${row.description}-${row.amount}-${index}`}>
                <td className="px-3 py-2">{formatDate(row.occurred_at)}</td>
                <td className="px-3 py-2">{row.transaction_type}</td>
                <td className="px-3 py-2">{row.category_id}</td>
                <td className="px-3 py-2">{row.description}</td>
                <td className="px-3 py-2">{formatCurrency(row.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4">
        <button type="button" className="btn-primary" onClick={onConfirm} disabled={loading}>
          {loading ? 'Confirming...' : `Import ${data.summary.records_valid} Transactions`}
        </button>
      </div>
    </section>
  )
}
