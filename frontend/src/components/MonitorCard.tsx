import type { Monitor } from '../types'
import { formatRelativeTime } from '../utils/time'
import { StatusBadge } from './StatusBadge'

const TYPE_LABELS: Record<Monitor['type'], string> = {
  http: 'HTTP',
  tcp: 'TCP',
  ping: 'PING',
  postgres: 'PG',
  redis: 'REDIS',
}

export function MonitorCard({ monitor }: { monitor: Monitor }) {
  const isCritical = monitor.status === 'down'
  const isQuiet = monitor.status === 'up' || monitor.status === 'unknown'

  return (
    <article
      className={`card card--${monitor.status}${isCritical ? ' card--critical' : ''}${isQuiet ? ' card--quiet' : ''}`}
    >
      <header className="card__header">
        <div className="card__title-row">
          <span className="card__index" aria-hidden="true">
            {String(monitor.id).padStart(2, '0')}
          </span>
          <h3 className="card__title">{monitor.name}</h3>
        </div>
        <StatusBadge status={monitor.status} />
      </header>

      <p className="card__target" title={monitor.target}>
        {monitor.target}
      </p>

      <div className="card__sparkline" aria-hidden="true">
        {Array.from({ length: 12 }, (_, i) => (
          <span
            key={i}
            className="card__sparkline-bar"
            style={{ height: `${20 + ((monitor.id * 7 + i * 13) % 60)}%` }}
          />
        ))}
      </div>

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
    </article>
  )
}
