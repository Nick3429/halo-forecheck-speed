// The effect's dependency list is supplied by the caller, which this rule can't verify statically
/* oxlint-disable react-hooks/exhaustive-deps */
import { useEffect, useState } from 'react'

export interface ApiState<T> {
  data: T | undefined
  error: string | undefined
  loading: boolean
}

/**
 * Runs `load` whenever `deps` change and tracks its result.
 * Superseded requests are aborted, so a slow old response never overwrites a newer one.
 */
export function useApi<T>(load: (signal: AbortSignal) => Promise<T>, deps: unknown[]): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({ data: undefined, error: undefined, loading: true })

  useEffect(() => {
    const controller = new AbortController()
    setState((prev) => ({ ...prev, error: undefined, loading: true }))
    load(controller.signal)
      .then((data) => setState({ data, error: undefined, loading: false }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        const message = err instanceof Error ? err.message : String(err)
        setState({ data: undefined, error: message, loading: false })
      })
    return () => controller.abort()
  }, deps)

  return state
}
