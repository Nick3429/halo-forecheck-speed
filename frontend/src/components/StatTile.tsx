import type { ReactNode } from 'react'

interface StatTileProps {
  label: string
  value: ReactNode
  detail?: ReactNode
  hover?: boolean
}

/** A card with a small label, one prominent value and an optional line underneath. */
export default function StatTile({ label, value, detail, hover = false }: StatTileProps) {
  return (
    <div className={`card flex h-full flex-col justify-center p-6 ${hover ? 'card-hover' : ''}`}>
      <span className="text-sm text-ink-2">{label}</span>
      <span className="mt-1 text-4xl font-semibold leading-tight">{value}</span>
      {detail && <span className="mt-2 text-sm text-ink-3">{detail}</span>}
    </div>
  )
}
