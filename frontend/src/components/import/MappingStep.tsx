interface MappingStepProps {
  columnsDetected: string[]
  mapping: Record<string, string>
  loading: boolean
  onMappingChange: (field: string, sourceColumn: string) => void
  onSubmit: () => void
}

const SYSTEM_FIELDS = ['occurred_at', 'transaction_type', 'category', 'description', 'amount', 'notes']

export function MappingStep({ columnsDetected, mapping, loading, onMappingChange, onSubmit }: MappingStepProps) {
  return (
    <section className="card">
      <h2 className="text-lg font-medium">2) Map columns</h2>
      <p className="mt-1 text-sm text-slate-500">Review and adjust file-to-system field mappings.</p>

      <div className="mt-4 grid gap-3">
        {SYSTEM_FIELDS.map((field) => (
          <div key={field} className="grid gap-2 md:grid-cols-2 md:items-center">
            <label className="text-sm font-medium capitalize text-slate-700">{field.replace('_', ' ')}</label>
            <select
              className="field"
              value={mapping[field] ?? ''}
              onChange={(event) => onMappingChange(field, event.target.value)}
            >
              <option value="">Select column</option>
              {columnsDetected.map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>

      <div className="mt-4">
        <button type="button" className="btn-primary" onClick={onSubmit} disabled={loading}>
          {loading ? 'Validating...' : 'Validate mapping'}
        </button>
      </div>
    </section>
  )
}
