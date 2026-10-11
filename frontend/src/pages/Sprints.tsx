import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { AXIS, CARD_SURFACE, SPRINT_BUCKETS } from '../chartTheme'
import ChartTooltip from '../components/ChartTooltip'
import PageHeader from '../components/PageHeader'
import PillGroup from '../components/PillGroup'
import { EmptyMessage, ErrorMessage, Loading } from '../components/Status'
import { count, displayName } from '../format'
import { useApi } from '../hooks/useApi'
import type { SprintRow, SprintSort } from '../types'

const CHART_ROWS = 15

const SORT_OPTIONS: { value: SprintSort; label: string }[] = [
  { value: 'sprints_22_plus_mph', label: '22+ mph' },
  { value: 'sprints_20_22_mph', label: '20–22 mph' },
  { value: 'sprints_18_20_mph', label: '18–20 mph' },
  { value: 'sprints_total', label: 'All sprints' },
]

const POSITION_OPTIONS = [
  { value: 'ALL', label: 'All' },
  { value: 'C', label: 'C' },
  { value: 'LW', label: 'LW' },
  { value: 'RW', label: 'RW' },
  { value: 'F', label: 'F' },
  { value: 'D', label: 'D' },
]

// Sortable count columns in the table, fastest bucket first
const TABLE_COLUMNS: { key: SprintSort; label: string }[] = [
  { key: 'sprints_22_plus_mph', label: '22+ mph' },
  { key: 'sprints_20_22_mph', label: '20–22 mph' },
  { key: 'sprints_18_20_mph', label: '18–20 mph' },
  { key: 'sprints_total', label: 'Total' },
]

/** Column header that ranks the table by its column when clicked. */
function SortableHeader({ column, label, sort, onSort }: { column: SprintSort; label: string; sort: SprintSort; onSort: (column: SprintSort) => void }) {
  const active = column === sort
  return (
    <th className="num" aria-sort={active ? 'descending' : 'none'}>
      <button type="button" className={`sort-header ${active ? 'active' : ''}`} onClick={() => onSort(column)}>
        {label}
        <span className="sort-arrow" aria-hidden="true">
          ▼
        </span>
      </button>
    </th>
  )
}

/** Stack order: the ranked bucket sits on the baseline so rows can be compared by it; the rest follow fastest-first. */
function stackOrder(sort: SprintSort) {
  const fastestFirst = [...SPRINT_BUCKETS].reverse()
  if (sort === 'sprints_total') return fastestFirst
  return [...fastestFirst.filter((b) => b.key === sort), ...fastestFirst.filter((b) => b.key !== sort)]
}

/** Legend in the same left-to-right order as the stacked segments. */
function Legend({ order }: { order: ReturnType<typeof stackOrder> }) {
  return (
    <div className="flex flex-wrap gap-5 text-sm text-ink-2">
      {order.map((bucket) => (
        <span key={bucket.key} className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-sm" style={{ background: bucket.color }} />
          {bucket.label}
        </span>
      ))}
    </div>
  )
}

export default function Sprints() {
  const navigate = useNavigate()
  const [sort, setSort] = useState<SprintSort>('sprints_22_plus_mph')
  const [position, setPosition] = useState('ALL')

  const { data, error, loading } = useApi(
    (signal) =>
      api.sprintLeaderboard({ sort_by: sort, position: position === 'ALL' ? undefined : position, limit: 1000 }, signal),
    [sort, position],
  )

  const sortLabel = SORT_OPTIONS.find((o) => o.value === sort)!.label
  const chartData = (data ?? []).slice(0, CHART_ROWS).map((row) => ({ ...row, name: displayName(row.player_name) }))
  const order = stackOrder(sort)
  const openPlayer = (playerId: string) => navigate(`/players/${playerId}`)

  return (
    <section className="fade-in-up mx-auto max-w-6xl px-6 pb-16">
      <PageHeader title="Sprint Leaderboard">
        A sprint is a run of skating at 18 mph or faster, counted once and bucketed by the top speed reached. Speeds come
        from tracking snapshots taken at each event, so these are sprints observed at events.
      </PageHeader>

      <div className="mb-10 flex flex-wrap items-start justify-center gap-x-10 gap-y-6">
        <PillGroup label="Rank by" options={SORT_OPTIONS} value={sort} onChange={setSort} />
        <PillGroup label="Position" options={POSITION_OPTIONS} value={position} onChange={setPosition} />
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
            <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="mb-1 text-xl font-bold">Top {chartData.length} by {sortLabel === 'All sprints' ? 'total sprints' : `${sortLabel} sprints`}</h2>
                <p className="text-sm text-ink-3">Bar length is total sprints. Select a bar to open the player.</p>
              </div>
              <Legend order={order} />
            </div>
            <ResponsiveContainer width="100%" height={chartData.length * 34 + 40}>
              <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 56, bottom: 0, left: 0 }}>
                <CartesianGrid horizontal={false} stroke={AXIS.grid} />
                <XAxis type="number" tick={AXIS.tick} tickLine={false} axisLine={{ stroke: AXIS.line }} allowDecimals={false} />
                <YAxis type="category" dataKey="name" width={160} tick={AXIS.categoryTick} tickLine={false} axisLine={false} />
                <Tooltip
                  cursor={AXIS.cursor}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null
                    const row = payload[0].payload as SprintRow & { name: string }
                    return (
                      <ChartTooltip
                        title={row.name}
                        rows={[...SPRINT_BUCKETS].reverse().map((b) => ({ label: b.label, value: count(row[b.key]), color: b.color }))}
                        footer={`${count(row.sprints_total)} sprints in total`}
                      />
                    )
                  }}
                />
                {order.map((bucket, i) => (
                  <Bar
                    key={bucket.key}
                    dataKey={bucket.key}
                    name={bucket.label}
                    stackId="sprints"
                    fill={bucket.color}
                    stroke={CARD_SURFACE}
                    strokeWidth={2}
                    barSize={20}
                    radius={i === order.length - 1 ? [0, 4, 4, 0] : 0}
                    cursor="pointer"
                    isAnimationActive={false}
                    onClick={(entry) => openPlayer((entry as unknown as { payload: SprintRow }).payload.player_id)}
                  >
                    {i === order.length - 1 && (
                      <LabelList dataKey="sprints_total" position="right" fill={AXIS.label} fontSize={12} />
                    )}
                  </Bar>
                ))}
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
                  {TABLE_COLUMNS.map((col) => (
                    <SortableHeader key={col.key} column={col.key} label={col.label} sort={sort} onSort={setSort} />
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr key={row.player_id} onClick={() => openPlayer(row.player_id)}>
                    <td className="num text-ink-3">{i + 1}</td>
                    <td className="font-medium">{displayName(row.player_name)}</td>
                    <td className="text-ink-2">{row.primary_position ?? '—'}</td>
                    {TABLE_COLUMNS.map((col) => (
                      <td key={col.key} className={`num ${col.key === sort ? 'font-semibold' : 'text-ink-2'}`}>
                        {count(row[col.key])}
                      </td>
                    ))}
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
