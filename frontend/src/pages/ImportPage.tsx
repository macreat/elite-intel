import { useState } from 'react'
import { ErrorState } from '../components/common/States'
import { MappingStep } from '../components/import/MappingStep'
import { PreviewStep } from '../components/import/PreviewStep'
import { UploadStep } from '../components/import/UploadStep'
import { ValidationReportStep } from '../components/import/ValidationReportStep'
import { apiClient } from '../services/apiClient'
import type { ImportMappingResponse, ImportUploadResponse } from '../types/import'

type Step = 'upload' | 'mapping' | 'validation' | 'preview' | 'success'

export function ImportPage() {
  const [step, setStep] = useState<Step>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [uploadData, setUploadData] = useState<ImportUploadResponse | null>(null)
  const [mappingData, setMappingData] = useState<ImportMappingResponse | null>(null)
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmResult, setConfirmResult] = useState<{ batch_id: number; records_inserted: number } | null>(null)

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.uploadImportFile(file)
      setUploadData(result)
      setMapping(result.suggested_mapping ?? {})
      setStep('mapping')
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Failed to upload file')
    } finally {
      setLoading(false)
    }
  }

  const handleValidate = async () => {
    if (!uploadData) return
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.submitImportMapping(uploadData.batch_id, { mapping })
      setMappingData(result)
      setStep('validation')
    } catch (mappingError) {
      setError(mappingError instanceof Error ? mappingError.message : 'Failed to validate mapping')
    } finally {
      setLoading(false)
    }
  }

  const moveToPreview = () => {
    setStep('preview')
  }

  const handleConfirm = async () => {
    if (!mappingData) return
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.confirmImport(mappingData.batch_id)
      setConfirmResult({ batch_id: result.batch_id, records_inserted: result.records_inserted })
      setStep('success')
    } catch (confirmError) {
      setError(confirmError instanceof Error ? confirmError.message : 'Failed to confirm import')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">Import Transactions</h1>
        <p className="text-sm text-slate-500">Upload, map, validate, preview, and confirm your historical data import.</p>
      </header>

      {error ? <ErrorState title="Import error" message={error} /> : null}

      {step === 'upload' ? (
        <UploadStep file={file} loading={loading} onFileSelect={setFile} onUpload={handleUpload} />
      ) : null}

      {step === 'mapping' && uploadData ? (
        <MappingStep
          columnsDetected={uploadData.columns_detected}
          mapping={mapping}
          loading={loading}
          onMappingChange={(field, sourceColumn) => setMapping((prev) => ({ ...prev, [field]: sourceColumn }))}
          onSubmit={handleValidate}
        />
      ) : null}

      {step === 'validation' && mappingData ? (
        <div className="space-y-4">
          <ValidationReportStep data={mappingData} />
          <div>
            <button type="button" className="btn-primary" onClick={moveToPreview}>
              Continue to Preview
            </button>
          </div>
        </div>
      ) : null}

      {step === 'preview' && mappingData ? (
        <PreviewStep data={mappingData} loading={loading} onConfirm={handleConfirm} />
      ) : null}

      {step === 'success' && confirmResult ? (
        <section className="card">
          <h2 className="text-lg font-medium text-emerald-700">Import completed</h2>
          <p className="mt-2 text-sm text-slate-600">
            Batch #{confirmResult.batch_id} inserted {confirmResult.records_inserted} transaction(s).
          </p>
          <div className="mt-4 flex gap-2">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                setStep('upload')
                setFile(null)
                setUploadData(null)
                setMappingData(null)
                setConfirmResult(null)
                setMapping({})
                setError(null)
              }}
            >
              Import another file
            </button>
          </div>
        </section>
      ) : null}
    </div>
  )
}
