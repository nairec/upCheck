import type { MonitorStatus } from '../types'

const LABELS: Record<MonitorStatus, string> = {
  up: 'OK',
  down: 'DOWN',
  degraded: 'WARN',
  unknown: '—',
}

export function StatusBadge({ status }: { status: MonitorStatus }) {
  return (
    <span className={`status-badge status-badge--${status}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      <span className="status-badge__label">{LABELS[status]}</span>
    </span>
  )
}
