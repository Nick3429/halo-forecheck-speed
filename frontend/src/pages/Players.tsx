import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import PageHeader from '../components/PageHeader'
import PillGroup from '../components/PillGroup'
import { EmptyMessage, ErrorMessage, Loading } from '../components/Status'
import { displayName, positionName } from '../format'
import { useApi } from '../hooks/useApi'

const PAGE_SIZE = 48

const POSITION_OPTIONS = [
  { value: 'ALL', label: 'All' },
  { value: 'C', label: 'C' },
  { value: 'LW', label: 'LW' },
  { value: 'RW', label: 'RW' },
  { value: 'F', label: 'F' },
  { value: 'D', label: 'D' },
  { value: 'G', label: 'G' },
]

export default function Players() {
  const [search, setSearch] = useState('')
  const [position, setPosition] = useState('ALL')
  const [shown, setShown] = useState(PAGE_SIZE)

  // The full player list is small, so load it once and filter in the browser
  const { data, error, loading } = useApi((signal) => api.players({}, signal), [])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return (data ?? []).filter(
      (p) =>
        (position === 'ALL' || p.primary_position === position) &&
        (!term || displayName(p.player_name).toLowerCase().includes(term)),
    )
  }, [data, search, position])

  const updateFilter = (apply: () => void) => {
    apply()
    setShown(PAGE_SIZE)
  }

  return (
    <section className="fade-in-up mx-auto max-w-6xl px-6 pb-16">
      <PageHeader title="Players">Search for a player to see their forecheck and sprint profile.</PageHeader>

      <div className="mb-10 flex flex-col items-center gap-6">
        <input
          type="search"
          value={search}
          onChange={(e) => updateFilter(() => setSearch(e.target.value))}
          placeholder="Search by name"
          aria-label="Search players by name"
          className="w-full max-w-md rounded-full border border-white/30 bg-white/10 px-6 py-3 text-ink placeholder:text-ink-3 focus:border-white/70 focus:outline-none"
        />
        <PillGroup
          label="Position"
          options={POSITION_OPTIONS}
          value={position}
          onChange={(v) => updateFilter(() => setPosition(v))}
        />
      </div>

      {error ? (
        <ErrorMessage message={error} />
      ) : loading ? (
        <Loading />
      ) : !filtered.length ? (
        <EmptyMessage>No players match “{search}”.</EmptyMessage>
      ) : (
        <>
          <p className="mb-4 text-sm text-ink-3">
            Showing {Math.min(shown, filtered.length)} of {filtered.length} players
          </p>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.slice(0, shown).map((player) => (
              <Link key={player.player_id} to={`/players/${player.player_id}`} className="card card-hover block p-6">
                <h3 className="text-lg font-bold">{displayName(player.player_name)}</h3>
                <p className="text-sm text-ink-2">{positionName(player.primary_position)}</p>
              </Link>
            ))}
          </div>
          {shown < filtered.length && (
            <div className="mt-10 text-center">
              <button type="button" className="pill-btn" onClick={() => setShown((n) => n + PAGE_SIZE)}>
                Show more
              </button>
            </div>
          )}
        </>
      )}
    </section>
  )
}
