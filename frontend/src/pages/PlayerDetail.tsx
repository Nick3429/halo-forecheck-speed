import { Link, useParams } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { AXIS, SPRINT_BUCKETS } from '../chartTheme'
import ChartTooltip from '../components/ChartTooltip'
import StatTile from '../components/StatTile'
import { ErrorMessage, Loading } from '../components/Status'
import { count, displayName, percent, positionName } from '../format'
import { useApi } from '../hooks/useApi'
import type { SprintStats } from '../types'

function SprintChart({ sprints }: { sprints: SprintStats }) {
  const data = SPRINT_BUCKETS.map((b) => ({ label: b.label, value: sprints[b.key], color: b.color }))
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 24, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} stroke={AXIS.grid} />
        <XAxis dataKey="label" tick={AXIS.categoryTick} tickLine={false} axisLine={{ stroke: AXIS.line }} />
        <YAxis tick={AXIS.tick} tickLine={false} axisLine={false} allowDecimals={false} width={40} />
        <Tooltip
          cursor={AXIS.cursor}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const row = payload[0].payload as (typeof data)[number]
            return <ChartTooltip title={row.label} rows={[{ label: 'Sprints', value: count(row.value), color: row.color }]} />
          }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={24} isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.label} fill={d.color} />
          ))}
          <LabelList dataKey="value" position="top" fill={AXIS.label} fontSize={12} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

function Placeholder({ children }: { children: string }) {
  return <p className="card p-6 italic text-ink-3">{children}</p>
}

export default function PlayerDetail() {
  const { playerId = '' } = useParams()
  const { data: player, error, loading } = useApi((signal) => api.player(playerId, signal), [playerId])

  return (
    <section className="fade-in-up mx-auto max-w-5xl px-6 pb-16">
      <Link to="/players" className="pill-btn mb-8">
        ← All players
      </Link>

      {error ? (
        <ErrorMessage message={error} />
      ) : loading || !player ? (
        <Loading />
      ) : (
        <div className="space-y-12">
          <header className="text-center">
            <p className="text-sm uppercase tracking-[3px] text-ink-3">{positionName(player.primary_position)}</p>
            <h1 className="section-title title-rule mt-1">{displayName(player.player_name)}</h1>
          </header>

          <div>
            <h2 className="mb-4 text-2xl font-bold">F1 forecheck</h2>
            {player.forecheck ? (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                <StatTile label="Success rate" value={percent(player.forecheck.success_rate)} detail="Recoveries ÷ F1 attempts" />
                <StatTile label="Recoveries" value={count(player.forecheck.recoveries)} detail="Forechecks that won the puck" />
                <StatTile label="F1 attempts" value={count(player.forecheck.attempts)} detail="Times closest to the puck" />
              </div>
            ) : (
              <Placeholder>
                No F1 forecheck record. Players need at least 10 F1 attempts on high-pressure dump-ins to be ranked.
              </Placeholder>
            )}
          </div>

          <div>
            <h2 className="mb-4 text-2xl font-bold">Sprints</h2>
            {player.sprints ? (
              <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                <StatTile label="Total sprints" value={count(player.sprints.sprints_total)} detail="Runs at 18 mph or faster" />
                <div className="card p-6 md:col-span-2">
                  <h3 className="mb-1 font-semibold">Sprints by top speed</h3>
                  <SprintChart sprints={player.sprints} />
                </div>
              </div>
            ) : (
              <Placeholder>No sprints recorded. Goalies are excluded, and some players never reached 18 mph.</Placeholder>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
