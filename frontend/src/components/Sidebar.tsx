import type { DashboardStats } from '../types'

interface SidebarProps {
  monitorCount: number
}

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', active: true },
  { id: 'monitors', label: 'Monitores', active: false },
  { id: 'incidents', label: 'Incidentes', active: false, soon: true },
  { id: 'alerts', label: 'Alertas', active: false, soon: true },
]

export function Sidebar({ monitorCount }: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="Navegación principal">
      <div className="sidebar__brand">
        <span className="sidebar__mark" aria-hidden="true">
          ◈
        </span>
        <div>
          <p className="sidebar__title">upCheck</p>
          <p className="sidebar__tag">control room</p>
        </div>
      </div>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <span
            key={item.id}
            className={`sidebar__link${item.active ? ' sidebar__link--active' : ''}${item.soon ? ' sidebar__link--soon' : ''}`}
            aria-current={item.active ? 'page' : undefined}
          >
            <span className="sidebar__link-label">{item.label}</span>
            {item.soon && <span className="sidebar__soon">pronto</span>}
          </span>
        ))}
      </nav>

      <div className="sidebar__footer">
        <p className="sidebar__stat">
          <span className="sidebar__stat-value">{monitorCount}</span>
          <span className="sidebar__stat-label">monitores activos</span>
        </p>
        <p className="sidebar__version">v0.1 · ops</p>
      </div>
    </aside>
  )
}

export function HealthBar({ stats }: { stats: DashboardStats }) {
  const { monitors, uptime_24h_percent } = stats
  const hasIssues = monitors.down > 0 || monitors.degraded > 0
  const healthPercent =
    uptime_24h_percent ??
    (monitors.total > 0 ? Math.round((monitors.up / monitors.total) * 100) : 100)
  const barClass = hasIssues
    ? monitors.down > 0
      ? 'health-bar__fill--down'
      : 'health-bar__fill--degraded'
    : 'health-bar__fill--ok'

  return (
    <section className="health-bar" aria-label="Salud del sistema">
      <div className="health-bar__header">
        <span className="health-bar__label">system health</span>
        <span className={`health-bar__status${hasIssues ? ' health-bar__status--alert' : ''}`}>
          {hasIssues
            ? monitors.down > 0
              ? `${monitors.down} servicio${monitors.down > 1 ? 's' : ''} caído${monitors.down > 1 ? 's' : ''}`
              : `${monitors.degraded} degradado${monitors.degraded > 1 ? 's' : ''}`
            : 'todos los sistemas operativos'}
        </span>
      </div>
      <div className="health-bar__track" role="progressbar" aria-valuenow={healthPercent} aria-valuemin={0} aria-valuemax={100}>
        <div className={`health-bar__fill ${barClass}`} style={{ width: `${healthPercent}%` }} />
      </div>
      <div className="health-bar__meta">
        <span>uptime 24h · {uptime_24h_percent != null ? `${uptime_24h_percent.toFixed(1)}%` : '—'}</span>
        <span>
          {monitors.up}/{monitors.total} operativos
        </span>
      </div>
    </section>
  )
}
