import type { Monitor } from '../types'
import { StatusBadge } from './StatusBadge'

const TYPE_LABELS: Record<Monitor['type'], string> = {
  http: 'HTTP',
  tcp: 'TCP',
  ping: 'Ping',
  postgres: 'PostgreSQL',
  redis: 'Redis',
}

export function MonitorCard({ monitor }: { monitor: Monitor }) {
  return (
    <article className={`card card--${monitor.status}`}>
      <header className="card__header">
        <h3 className="card__title">{monitor.name}</h3>
        <StatusBadge status={monitor.status} />
      </header>

      <p className="card__target" title={monitor.target}>
        {monitor.target}
      </p>

      <footer className="card__meta">
        <span className="tag">{TYPE_LABELS[monitor.type]}</span>
        <span>cada {monitor.interval_seconds}s</span>
        <span>
          {monitor.response_time_ms != null
            ? `${monitor.response_time_ms.toFixed(0)} ms`
            : '— ms'}
        </span>
      </footer>
    </article>
  )
}
