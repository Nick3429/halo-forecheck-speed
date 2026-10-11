import type { ReactNode } from 'react'

export interface TooltipRow {
  label: string
  value: string
  color?: string
}

/** Dark card used as the hover tooltip in every chart. Colour appears only as a swatch, never on text. */
export default function ChartTooltip({ title, rows, footer }: { title: string; rows: TooltipRow[]; footer?: ReactNode }) {
  return (
    <div className="rounded-xl border border-hairline bg-[#111111]/95 px-4 py-3 text-sm shadow-2xl">
      <div className="mb-1 font-semibold">{title}</div>
      {rows.map((row) => (
        <div key={row.label} className="flex items-center justify-between gap-6 tabular-nums">
          <span className="flex items-center gap-2 text-ink-2">
            {row.color && <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: row.color }} />}
            {row.label}
          </span>
          <span>{row.value}</span>
        </div>
      ))}
      {footer && <div className="mt-2 text-xs text-ink-3">{footer}</div>}
    </div>
  )
}
