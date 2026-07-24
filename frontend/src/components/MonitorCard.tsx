import { Link } from 'react-router-dom'
import type { Monitor } from '../types'
import { formatMonitorIndex } from '../utils/monitors'
import { formatRelativeTime } from '../utils/time'
import { Sparkline } from './Sparkline'
import { StatusBadge } from './StatusBadge'

const TYPE_LABELS: Record<Monitor['type'], string> = {
  http: 'HTTP',
  tcp: 'TCP',
  ping: 'PING',
  postgres: 'PG',
  redis: 'REDIS',
}

export function MonitorCard({ monitor, displayIndex }: { monitor: Monitor; displayIndex: number }) {
  const isCritical = monitor.status === 'down'
  const isQuiet = monitor.status === 'up' || monitor.status === 'unknown'
  const recentChecks = monitor.recent_checks ?? []

  return (
    <Link
      to={`/monitors/${monitor.id}`}
      className={`card card--link card--${monitor.status}${isCritical ? ' card--critical' : ''}${isQuiet ? ' card--quiet' : ''}`}
    >
      <header className="card__header">
        <div className="card__title-row">
          <span className="card__index" aria-hidden="true">
            {formatMonitorIndex(displayIndex)}
          </span>
          <h3 className="card__title">{monitor.name}</h3>
        </div>
        <StatusBadge status={monitor.status} />
      </header>

      <p className="card__target" title={monitor.target}>
        {monitor.target}
      </p>

      <Sparkline points={recentChecks} className="card__sparkline" />

      <footer className="card__meta">
        <span className="tag">{TYPE_LABELS[monitor.type]}</span>
        <span className="card__interval">/{monitor.interval_seconds}s</span>
        <span className="card__latency">
          {monitor.response_time_ms != null
            ? `${monitor.response_time_ms.toFixed(0)}ms`
            : '—ms'}
        </span>
        <span className="card__time">{formatRelativeTime(monitor.last_checked_at)}</span>
      </footer>
    </Link>
  )
}
