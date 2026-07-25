import { Link, useLocation } from 'react-router-dom'
import type { DashboardStats } from '../types'

interface SidebarProps {
  monitorCount: number
  openIncidentCount: number
}

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', path: '/', soon: false },
  { id: 'alerts', label: 'Alertas', path: '/alerts', soon: false },
  { id: 'incidents', label: 'Incidentes', path: '/incidents', soon: false },
]

export function Sidebar({ monitorCount, openIncidentCount }: SidebarProps) {
  const location = useLocation()

  return (
    <aside className="sidebar" aria-label="Navegación principal">
      <Link to="/" className="sidebar__brand">
        <span className="sidebar__mark" aria-hidden="true">
          ◈
        </span>
        <div>
          <p className="sidebar__title">upCheck</p>
        </div>
      </Link>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.path === '/'
              ? location.pathname === '/'
              : item.path !== '#' && location.pathname.startsWith(item.path)
          const className = `sidebar__link${isActive ? ' sidebar__link--active' : ''}${item.soon ? ' sidebar__link--soon' : ''}`

          if (item.soon) {
            return (
              <span key={item.id} className={className}>
                <span className="sidebar__link-label">{item.label}</span>
                <span className="sidebar__soon">pronto</span>
              </span>
            )
          }

          return (
            <Link
              key={item.id}
              to={item.path}
              className={className}
              aria-current={isActive ? 'page' : undefined}
            >
              <span className="sidebar__link-label">{item.label}</span>
              {item.id === 'incidents' && openIncidentCount > 0 && (
                <span className="sidebar__badge" aria-label={`${openIncidentCount} incidentes activos`} />
              )}
            </Link>
          )
        })}
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
