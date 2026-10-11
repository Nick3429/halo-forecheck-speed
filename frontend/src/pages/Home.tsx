import { Link } from 'react-router-dom'
import { api } from '../api'
import StatTile from '../components/StatTile'
import { ErrorMessage, Loading } from '../components/Status'
import { count, displayName, percent } from '../format'
import { useApi } from '../hooks/useApi'
import type { ForecheckRow, SprintRow } from '../types'

interface Leaders {
  bestRate: ForecheckRow
  mostRecoveries: ForecheckRow
  most22Plus: SprintRow
  mostSprints: SprintRow
}

async function loadLeaders(signal: AbortSignal): Promise<Leaders> {
  const [bestRate, mostRecoveries, most22Plus, mostSprints] = await Promise.all([
    api.forecheckLeaderboard({ sort_by: 'success_rate', limit: 1 }, signal),
    api.forecheckLeaderboard({ sort_by: 'recoveries', limit: 1 }, signal),
    api.sprintLeaderboard({ sort_by: 'sprints_22_plus_mph', limit: 1 }, signal),
    api.sprintLeaderboard({ sort_by: 'sprints_total', limit: 1 }, signal),
  ])
  return { bestRate: bestRate[0], mostRecoveries: mostRecoveries[0], most22Plus: most22Plus[0], mostSprints: mostSprints[0] }
}

function LeaderTile({ label, value, playerId, playerName }: { label: string; value: string; playerId: string; playerName: string | null }) {
  return (
    <Link to={`/players/${playerId}`} className="block h-full">
      <StatTile label={label} value={value} detail={displayName(playerName)} hover />
    </Link>
  )
}

export default function Home() {
  const { data: leaders, error, loading } = useApi(loadLeaders, [])

  return (
    <section className="grid min-h-[calc(100vh-6rem)] grid-cols-1 items-center gap-12 px-6 pb-16 lg:grid-cols-2 lg:px-12">
      <div className="fade-in-up mx-auto max-w-xl text-center">
        <p className="text-2xl uppercase tracking-[3px] text-ink-3">AHL · 2023–24</p>
        <h1 className="title-rule mt-1 text-6xl font-extrabold tracking-wide md:text-7xl">HALO</h1>
        <p className="mt-6 text-lg text-ink-2">
          Forecheck effectiveness and skating speed for every AHL skater, built from one season of player tracking.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link to="/forecheck" className="pill-btn">
            Forecheck leaderboard
          </Link>
          <Link to="/sprints" className="pill-btn">
            Sprint leaderboard
          </Link>
          <Link to="/players" className="pill-btn">
            Find a player
          </Link>
        </div>
      </div>

      <div className="fade-in-up mx-auto w-full max-w-xl [animation-delay:150ms]">
        {error ? (
          <ErrorMessage message={error} />
        ) : loading || !leaders ? (
          <Loading label="Loading leaders…" />
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <LeaderTile
              label="Best F1 success rate"
              value={percent(leaders.bestRate.success_rate)}
              playerId={leaders.bestRate.player_id}
              playerName={leaders.bestRate.player_name}
            />
            <LeaderTile
              label="Most F1 recoveries"
              value={count(leaders.mostRecoveries.recoveries)}
              playerId={leaders.mostRecoveries.player_id}
              playerName={leaders.mostRecoveries.player_name}
            />
            <LeaderTile
              label="Most 22+ mph sprints"
              value={count(leaders.most22Plus.sprints_22_plus_mph)}
              playerId={leaders.most22Plus.player_id}
              playerName={leaders.most22Plus.player_name}
            />
            <LeaderTile
              label="Most sprints overall"
              value={count(leaders.mostSprints.sprints_total)}
              playerId={leaders.mostSprints.player_id}
              playerName={leaders.mostSprints.player_name}
            />
          </div>
        )}
      </div>
    </section>
  )
}
