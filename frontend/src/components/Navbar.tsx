import { useEffect, useState, type CSSProperties, type ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'

interface NavItem {
  to: string
  label: string
  accent?: string
  icon: ReactNode
}

const iconProps = {
  className: 'link-icon',
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/',
    label: 'Home',
    icon: (
      <svg {...iconProps}>
        <path d="M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3z" />
      </svg>
    ),
  },
  {
    to: '/forecheck',
    label: 'Forecheck',
    icon: (
      <svg {...iconProps}>
        <circle cx="12" cy="12" r="9" />
        <circle cx="12" cy="12" r="5" />
        <circle cx="12" cy="12" r="1" />
      </svg>
    ),
  },
  {
    to: '/sprints',
    label: 'Sprints',
    icon: (
      <svg {...iconProps}>
        <path d="M13 2 4 14h7l-1 8 9-12h-7z" />
      </svg>
    ),
  },
  {
    to: '/players',
    label: 'Players',
    icon: (
      <svg {...iconProps}>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" />
      </svg>
    ),
  },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <nav className={`navbar ${scrolled ? 'navbar-scrolled' : ''}`}>
      <div className="flex flex-wrap items-center justify-between gap-y-2 px-[30px] md:relative">
        <Link to="/" className="logo">
          <svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true">
            <ellipse cx="12" cy="14" rx="9" ry="4" fill="currentColor" />
            <ellipse cx="12" cy="11" rx="9" ry="4" fill="none" stroke="currentColor" strokeWidth="2" />
          </svg>
          HALO
        </Link>

        <ul className="flex list-none gap-2 md:absolute md:left-1/2 md:-translate-x-1/2">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  ['nav-link', isActive ? 'active' : '', item.accent ? 'has-accent' : ''].join(' ')
                }
                style={item.accent ? ({ '--nav-accent': item.accent } as CSSProperties) : undefined}
              >
                {item.icon}
                <span className="hidden sm:inline">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>

        <span className="hidden text-sm text-ink-3 lg:block">AHL · 2023–24</span>
      </div>
    </nav>
  )
}
