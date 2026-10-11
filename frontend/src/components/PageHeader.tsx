import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  children?: ReactNode
}

/** Section title with the site's white rule underneath, plus an optional subtitle. */
export default function PageHeader({ title, children }: PageHeaderProps) {
  return (
    <header className="mb-10 text-center">
      <h1 className="section-title title-rule">{title}</h1>
      {children && <p className="mx-auto mt-5 max-w-2xl text-ink-2">{children}</p>}
    </header>
  )
}
