import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { AXIS, FORECHECK_BAR } from '../chartTheme'
import ChartTooltip from '../components/ChartTooltip'
import PageHeader from '../components/PageHeader'
import PillGroup from '../components/PillGroup'
import { EmptyMessage, ErrorMessage, Loading } from '../components/Status'
import { count, displayName, percent } from '../format'
import { useApi } from '../hooks/useApi'
import type { ForecheckRow, ForecheckSort } from '../types'

const CHART_ROWS = 15

const SORT_OPTIONS: { value: ForecheckSort; label: string }[] = [
  { value: 'success_rate', label: 'Success rate' },
  { value: 'recoveries', label: 'Recoveries' },
  { value: 'attempts', label: 'Attempts' },
]

const POSITION_OPTIONS = [
  { value: 'ALL', label: 'All' },
  { value: 'C', label: 'C' },
  { value: 'LW', label: 'LW' },
  { value: 'RW', label: 'RW' },
  { value: 'F', label: 'F' },
]

const MIN_ATTEMPT_OPTIONS = [
  { value: '10', label: '10+' },
  { value: '20', label: '20+' },
  { value: '30', label: '30+' },
]

function formatMetric(sort: ForecheckSort, value: number): string {
  return sort === 'success_rate' ? percent(value) : count(value)
}

export default function Forecheck() {
  const navigate = useNavigate()
  const [sort, setSort] = useState<ForecheckSort>('success_rate')
  const [position, setPosition] = useState('ALL')
  const [minAttempts, setMinAttempts] = useState('10')

  const { data, error, loading } = useApi(
    (signal) =>
      api.forecheckLeaderboard(
        { sort_by: sort, min_attempts: Number(minAttempts), position: position === 'ALL' ? undefined : position, limit: 500 },
        signal,
      ),
    [sort, position, minAttempts],
  )

  const sortLabel = SORT_OPTIONS.find((o) => o.value === sort)!.label
  const chartData = (data ?? []).slice(0, CHART_ROWS).map((row) => ({ ...row, name: displayName(row.player_name) }))
  const openPlayer = (playerId: string) => navigate(`/players/${playerId}`)

  return (
    <section className="fade-in-up mx-auto max-w-6xl px-6 pb-16">
      <PageHeader title="F1 Forecheck Leaderboard">
        F1 is the forechecker closest to the puck on a high-pressure dump-in recovery. A recovery is credited when the
        retrieving team failed to come away with the puck.
      </PageHeader>

      <div className="mb-10 flex flex-wrap items-start justify-center gap-x-10 gap-y-6">
        <PillGroup label="Rank by" options={SORT_OPTIONS} value={sort} onChange={setSort} />
        <PillGroup label="Position" options={POSITION_OPTIONS} value={position} onChange={setPosition} />
        <PillGroup label="F1 attempts" options={MIN_ATTEMPT_OPTIONS} value={minAttempts} onChange={setMinAttempts} />
      </div>

      {error ? (
        <ErrorMessage message={error} />
      ) : loading && !data ? (
        <Loading />
      ) : !data?.length ? (
        <EmptyMessage>No players match these filters.</EmptyMessage>
      ) : (
        <div className={`space-y-8 transition-opacity ${loading ? 'opacity-50' : ''}`}>
          <div className="card p-6">
            <h2 className="mb-1 text-xl font-bold">Top {chartData.length} by {sortLabel.toLowerCase()}</h2>
            <p className="mb-4 text-sm text-ink-3">Select a bar to open the player.</p>
            <ResponsiveContainer width="100%" height={chartData.length * 34 + 40}>
              <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 64, bottom: 0, left: 0 }}>
                <CartesianGrid horizontal={false} stroke={AXIS.grid} />
                <XAxis
                  type="number"
                  domain={sort === 'success_rate' ? [0, 1] : [0, 'auto']}
                  tickFormatter={(v: number) => formatMetric(sort, v)}
                  tick={AXIS.tick}
                  tickLine={false}
                  axisLine={{ stroke: AXIS.line }}
                />
                <YAxis type="category" dataKey="name" width={160} tick={AXIS.categoryTick} tickLine={false} axisLine={false} />
                <Tooltip
                  cursor={AXIS.cursor}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null
                    const row = payload[0].payload as ForecheckRow & { name: string }
                    return (
                      <ChartTooltip
                        title={row.name}
                        rows={[
                          { label: 'Success rate', value: percent(row.success_rate) },
                          { label: 'Recoveries', value: count(row.recoveries) },
                          { label: 'F1 attempts', value: count(row.attempts) },
                        ]}
                      />
                    )
                  }}
                />
                <Bar
                  dataKey={sort}
                  fill={FORECHECK_BAR}
                  radius={[0, 4, 4, 0]}
                  barSize={18}
                  isAnimationActive={false}
                  cursor="pointer"
                  onClick={(entry) => openPlayer((entry as unknown as { payload: ForecheckRow }).payload.player_id)}
                >
                  <LabelList
                    dataKey={sort}
                    position="right"
                    fill={AXIS.label}
                    fontSize={12}
                    formatter={(v) => formatMetric(sort, Number(v))}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card overflow-x-auto p-2">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="num">#</th>
                  <th>Player</th>
                  <th>Pos</th>
                  <th className="num">F1 attempts</th>
                  <th className="num">Recoveries</th>
                  <th className="num">Success rate</th>
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr key={row.player_id} onClick={() => openPlayer(row.player_id)}>
                    <td className="num text-ink-3">{i + 1}</td>
                    <td className="font-medium">{displayName(row.player_name)}</td>
                    <td className="text-ink-2">{row.primary_position ?? '—'}</td>
                    <td className="num">{count(row.attempts)}</td>
                    <td className="num">{count(row.recoveries)}</td>
                    <td className="num">{percent(row.success_rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}
