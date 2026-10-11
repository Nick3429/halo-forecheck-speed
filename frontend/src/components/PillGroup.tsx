export interface PillOption<T extends string> {
  value: T
  label: string
}

interface PillGroupProps<T extends string> {
  label: string
  options: PillOption<T>[]
  value: T
  onChange: (value: T) => void
}

/** A row of pill buttons (the site's filter buttons) that behaves as a single-choice group. */
export default function PillGroup<T extends string>({ label, options, value, onChange }: PillGroupProps<T>) {
  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-xs uppercase tracking-wider text-ink-3">{label}</span>
      <div role="radiogroup" aria-label={label} className="flex flex-wrap justify-center gap-3">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={option.value === value}
            className={`pill-btn ${option.value === value ? 'active' : ''}`}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}
