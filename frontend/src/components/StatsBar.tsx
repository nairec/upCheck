import type { DashboardStats } from '../types'

interface StatItem {
  label: string
  value: string
  accent?: 'up' | 'down' | 'neutral'
}

export function StatsBar({ stats }: { stats: DashboardStats }) {
  const { monitors, uptime_24h_percent } = stats

  const items: StatItem[] = [
    { label: 'Monitores', value: String(monitors.total), accent: 'neutral' },
    { label: 'Operativos', value: String(monitors.up), accent: 'up' },
    { label: 'Caídos', value: String(monitors.down), accent: 'down' },
    {
      label: 'Uptime 24h',
      value: uptime_24h_percent != null ? `${uptime_24h_percent.toFixed(1)}%` : '—',
      accent: 'neutral',
    },
  ]

  return (
    <div className="stats">
      {items.map((item) => (
        <div key={item.label} className={`stats__item stats__item--${item.accent}`}>
          <span className="stats__value">{item.value}</span>
          <span className="stats__label">{item.label}</span>
        </div>
      ))}
    </div>
  )
}
