interface DeleteConfirmModalProps {
  open: boolean
  loading?: boolean
  title?: string
  onCancel: () => void
  onConfirm: () => void
}

export function DeleteConfirmModal({
  open,
  loading,
  title = 'Are you sure you want to delete this transaction? This action cannot be undone.',
  onCancel,
  onConfirm,
}: DeleteConfirmModalProps) {
  if (!open) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
        <h3 className="text-lg font-semibold">Confirm delete</h3>
        <p className="mt-2 text-sm text-slate-600">{title}</p>
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          <button type="button" className="btn-danger" onClick={onConfirm} disabled={loading}>
            {loading ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}
