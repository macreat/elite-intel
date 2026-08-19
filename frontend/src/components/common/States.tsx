interface MessageStateProps {
  title: string
  message: string
  action?: React.ReactNode
}

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="card flex items-center justify-center p-10 text-sm text-slate-400">
      <div className="flex items-center gap-3">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-mint-600 border-t-transparent" />
        {message}
      </div>
    </div>
  )
}

export function EmptyState({ title, message, action }: MessageStateProps) {
  return (
    <div className="card flex flex-col items-center gap-3 p-10 text-center">
      <h3 className="text-lg font-medium text-white">{title}</h3>
      <p className="max-w-md text-sm text-slate-400">{message}</p>
      {action}
    </div>
  )
}

export function ErrorState({ title, message, action }: MessageStateProps) {
  return (
    <div className="card border-rose-500/20 p-6">
      <h3 className="text-lg font-medium text-rose-400">{title}</h3>
      <p className="mt-2 text-sm text-rose-300/80">{message}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}
