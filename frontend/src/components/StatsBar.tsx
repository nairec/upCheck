import type { DashboardStats } from '../types'

interface StatItem {
  label: string
  value: string
  accent?: 'up' | 'down' | 'amber' | 'neutral'
}

export function StatsBar({ stats }: { stats: DashboardStats }) {
  const { monitors, uptime_24h_percent } = stats

  const items: StatItem[] = [
    { label: 'total', value: String(monitors.total).padStart(2, '0'), accent: 'neutral' },
    { label: 'operativos', value: String(monitors.up).padStart(2, '0'), accent: 'up' },
    { label: 'caídos', value: String(monitors.down).padStart(2, '0'), accent: 'down' },
    {
      label: 'uptime 24h',
      value: uptime_24h_percent != null ? `${uptime_24h_percent.toFixed(1)}%` : '—',
      accent: 'amber',
    },
  ]

  return (
    <div className="stats" role="list">
      {items.map((item) => (
        <div key={item.label} className={`stats__item stats__item--${item.accent}`} role="listitem">
          <span className="stats__label">{item.label}</span>
          <span className="stats__value">{item.value}</span>
        </div>
      ))}
    </div>
  )
}
