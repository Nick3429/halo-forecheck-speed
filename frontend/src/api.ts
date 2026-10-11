import type { ForecheckRow, ForecheckSort, Player, PlayerDetail, SprintRow, SprintSort } from './types'

// Set VITE_API_URL in frontend/.env.local to point at a different backend
export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function get<T>(path: string, params: Record<string, string | number | undefined>, signal?: AbortSignal): Promise<T> {
  const url = new URL(path, API_URL)
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') url.searchParams.set(key, String(value))
  }
  const response = await fetch(url, { signal })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ? String(body.detail) : `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  forecheckLeaderboard: (
    opts: { sort_by?: ForecheckSort; min_attempts?: number; position?: string; limit?: number },
    signal?: AbortSignal,
  ) => get<ForecheckRow[]>('/forecheck/leaderboard', opts, signal),

  sprintLeaderboard: (opts: { sort_by?: SprintSort; position?: string; limit?: number }, signal?: AbortSignal) =>
    get<SprintRow[]>('/sprints/leaderboard', opts, signal),

  players: (opts: { position?: string; search?: string }, signal?: AbortSignal) => get<Player[]>('/players', opts, signal),

  player: (playerId: string, signal?: AbortSignal) =>
    get<PlayerDetail>(`/players/${encodeURIComponent(playerId)}`, {}, signal),
}
