interface UploadStepProps {
  file: File | null
  loading: boolean
  onFileSelect: (file: File | null) => void
  onUpload: () => void
}

export function UploadStep({ file, loading, onFileSelect, onUpload }: UploadStepProps) {
  return (
    <section className="card">
      <h2 className="text-lg font-medium">1) Upload CSV or XLSX file</h2>
      <p className="mt-1 text-sm text-slate-500">
        Select a CSV or Excel (XLSX) file to start the import flow. Large Kardex/cuadernillo CSVs up to 250MB are supported.
        The original file will not be modified.
      </p>
      <div className="mt-4 rounded-lg border border-dashed border-slate-300 p-5">
        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={(event) => onFileSelect(event.target.files?.[0] ?? null)}
          className="block w-full text-sm"
        />
        <p className="mt-2 text-sm text-slate-600">{file ? `Selected: ${file.name}` : 'No file selected'}</p>
      </div>
      <div className="mt-4">
        <button type="button" className="btn-primary" disabled={!file || loading} onClick={onUpload}>
          {loading ? 'Uploading...' : 'Upload file'}
        </button>
      </div>
    </section>
  )
}
