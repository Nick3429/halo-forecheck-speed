import type { ReactNode } from 'react'
import { API_URL } from '../api'

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-ink-2" role="status">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-ink-3 border-t-transparent" />
      {label}
    </div>
  )
}

export function ErrorMessage({ message }: { message: string }) {
  const unreachable = message === 'Failed to fetch' || message.includes('NetworkError')
  return (
    <div className="card mx-auto max-w-xl p-8 text-center" role="alert">
      <h2 className="mb-2 text-xl font-bold">Couldn’t load this data</h2>
      <p className="text-ink-2">
        {unreachable
          ? `The API at ${API_URL} isn’t responding. Start it from the project root with: uvicorn backend.app.main:app --reload`
          : message}
      </p>
    </div>
  )
}

export function EmptyMessage({ children }: { children: ReactNode }) {
  return <p className="py-10 text-center italic text-ink-3">{children}</p>
}
