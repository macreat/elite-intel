import { useEffect, useState } from 'react'

interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useAsyncData<T>(loader: () => Promise<T>, deps: ReadonlyArray<unknown>): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    setLoading(true)
    setError(null)

    loader()
      .then((result) => {
        if (!mounted) return
        setData(result)
      })
      .catch((err: unknown) => {
        if (!mounted) return
        setError(err instanceof Error ? err.message : 'Unexpected error')
      })
      .finally(() => {
        if (!mounted) return
        setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, deps)

  return { data, loading, error }
}
