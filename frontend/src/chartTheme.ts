// Chart colours and chrome. Recharts sets SVG attributes, which can't read CSS variables, so they live here.
// All series colours were validated (dataviz palette validator, dark mode) against the #242424 card surface.

export const CARD_SURFACE = '#242424'

export const FORECHECK_BAR = '#c97d1c' // site orange (#fbb046) one step darker, inside the chart lightness band

// Ordinal teal ramp for sprint buckets: one hue, deeper = slower bucket
export const SPRINT_BUCKETS = [
  { key: 'sprints_18_20_mph', label: '18–20 mph', color: '#1d7a60' },
  { key: 'sprints_20_22_mph', label: '20–22 mph', color: '#3fb892' },
  { key: 'sprints_22_plus_mph', label: '22+ mph', color: '#9eeccf' },
] as const

export type SprintBucketKey = (typeof SPRINT_BUCKETS)[number]['key']

export const AXIS = {
  grid: '#333333',
  line: '#555555',
  tick: { fill: 'rgba(255, 255, 255, 0.5)', fontSize: 12 },
  categoryTick: { fill: 'rgba(255, 255, 255, 0.7)', fontSize: 13 },
  label: 'rgba(255, 255, 255, 0.7)',
  cursor: { fill: 'rgba(255, 255, 255, 0.05)' },
}
