import type { MonitorStatus } from '../types'

const LABELS: Record<MonitorStatus, string> = {
  up: 'Operativo',
  down: 'Caído',
  degraded: 'Degradado',
  unknown: 'Sin datos',
}

export function StatusBadge({ status }: { status: MonitorStatus }) {
  return <span className={`badge badge--${status}`}>{LABELS[status]}</span>
}
