import type { ImportMappingResponse } from '../../types/import'

interface ValidationReportStepProps {
  data: ImportMappingResponse
}

export function ValidationReportStep({ data }: ValidationReportStepProps) {
  return (
    <section className="card">
      <h2 className="text-lg font-medium text-white">3) Validation report</h2>
      <p className="mt-2 text-sm text-slate-400">
        {data.summary.records_valid} valid rows - {data.summary.records_invalid} invalid rows - {data.summary.records_duplicate} duplicates
      </p>

      {data.invalid_rows.length > 0 ? (
        <div className="mt-4 overflow-auto">
          <table className="min-w-full divide-y divide-white/[0.06] text-sm">
            <thead className="bg-navy-800/50 text-left text-xs uppercase text-slate-400">
              <tr>
                <th className="px-3 py-2">Row</th>
                <th className="px-3 py-2">Code</th>
                <th className="px-3 py-2">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {data.invalid_rows.map((row) => (
                <tr key={`${row.row_number}-${row.error_code}`} className="text-slate-300">
                  <td className="px-3 py-2">{row.row_number}</td>
                  <td className="px-3 py-2">{row.error_code}</td>
                  <td className="px-3 py-2">{row.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="mt-4 text-sm text-mint-500">No invalid rows found.</p>
      )}
    </section>
  )
}
