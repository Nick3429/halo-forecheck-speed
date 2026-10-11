import { useEffect } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar'
import Forecheck from './pages/Forecheck'
import Home from './pages/Home'
import PlayerDetail from './pages/PlayerDetail'
import Players from './pages/Players'
import Sprints from './pages/Sprints'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function NotFound() {
  return (
    <section className="fade-in-up py-24 text-center">
      <h1 className="section-title title-rule">Page not found</h1>
      <Link to="/" className="pill-btn mt-10">
        Back home
      </Link>
    </section>
  )
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Navbar />
      <main className="pt-28">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/forecheck" element={<Forecheck />} />
          <Route path="/sprints" element={<Sprints />} />
          <Route path="/players" element={<Players />} />
          <Route path="/players/:playerId" element={<PlayerDetail />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="p-8 text-center text-sm text-ink-3">
        HALO · AHL 2023–24 player tracking · Built with FastAPI, DuckDB and React
      </footer>
    </>
  )
}
