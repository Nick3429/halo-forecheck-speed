/** "Ratcliffe, Isaac" -> "Isaac Ratcliffe". Names without a comma are returned as-is. */
export function displayName(name: string | null | undefined): string {
  if (!name) return 'Unknown player'
  const [last, first] = name.split(',').map((part) => part.trim())
  return first ? `${first} ${last}` : last
}

export function percent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`
}

export function count(value: number): string {
  return value.toLocaleString('en-US')
}

const POSITION_NAMES: Record<string, string> = {
  C: 'Center',
  LW: 'Left wing',
  RW: 'Right wing',
  F: 'Forward',
  D: 'Defense',
  G: 'Goalie',
}

export function positionName(position: string | null | undefined): string {
  return position ? (POSITION_NAMES[position] ?? position) : 'Unknown position'
}
