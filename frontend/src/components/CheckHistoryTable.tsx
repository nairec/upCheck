import type { CheckResult } from '../types'
import { StatusBadge } from './StatusBadge'

interface CheckHistoryTableProps {
  items: CheckResult[]
  loading?: boolean
}

function formatTimestamp(iso: string): string {
  return new Date(iso).toISOString().replace('T', ' ').slice(0, 19)
}

export function CheckHistoryTable({ items, loading }: CheckHistoryTableProps) {
  if (loading) {
    return <p className="history-loading">Cargando historial…</p>
  }

  if (items.length === 0) {
    return (
      <p className="notice">
        <span className="notice__prefix">INFO</span>
        Sin ejecuciones registradas todavía.
      </p>
    )
  }

  return (
    <div className="history-table-wrap">
      <table className="history-table">
        <thead>
          <tr>
            <th scope="col">Hora (UTC)</th>
            <th scope="col">Estado</th>
            <th scope="col">Latencia</th>
            <th scope="col">HTTP</th>
            <th scope="col">Detalle</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className={`history-table__row history-table__row--${item.status}`}>
              <td className="history-table__time">{formatTimestamp(item.checked_at)}</td>
              <td>
                <StatusBadge status={item.status} />
              </td>
              <td className="history-table__mono">
                {item.response_time_ms != null ? `${item.response_time_ms.toFixed(0)} ms` : '—'}
              </td>
              <td className="history-table__mono">
                {item.status_code != null ? item.status_code : '—'}
              </td>
              <td className="history-table__error" title={item.error_message ?? undefined}>
                {item.error_message ?? '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
