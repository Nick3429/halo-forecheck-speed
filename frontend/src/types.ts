// Shapes returned by the FastAPI backend (see backend/app/schemas.py)

export interface Player {
  player_id: string
  player_name: string | null
  primary_position: string | null
}

export interface ForecheckStats {
  attempts: number
  recoveries: number
  success_rate: number
}

export interface SprintStats {
  sprints_18_20_mph: number
  sprints_20_22_mph: number
  sprints_22_plus_mph: number
  sprints_total: number
}

export type ForecheckRow = Player & ForecheckStats
export type SprintRow = Player & SprintStats

export interface PlayerDetail extends Player {
  forecheck: ForecheckStats | null
  sprints: SprintStats | null
}

export type ForecheckSort = 'success_rate' | 'attempts' | 'recoveries'
export type SprintSort = 'sprints_22_plus_mph' | 'sprints_20_22_mph' | 'sprints_18_20_mph' | 'sprints_total'
