import type { HistoryGranularity, HistoryPoint } from '../types'

interface AggregateHistoryTableProps {
  items: HistoryPoint[]
  granularity: HistoryGranularity
  loading?: boolean
}

function formatTimestamp(iso: string, granularity: HistoryGranularity): string {
  const date = new Date(iso)
  if (granularity === 'daily') {
    return date.toISOString().slice(0, 10)
  }
  return date.toISOString().replace('T', ' ').slice(0, 16)
}

export function AggregateHistoryTable({
  items,
  granularity,
  loading,
}: AggregateHistoryTableProps) {
  if (loading) {
    return <p className="history-loading">Cargando historial…</p>
  }

  if (items.length === 0) {
    return (
      <p className="notice">
        <span className="notice__prefix">INFO</span>
        Sin datos agregados en este rango.
      </p>
    )
  }

  return (
    <div className="history-table-wrap">
      <table className="history-table">
        <thead>
          <tr>
            <th scope="col">Periodo (UTC)</th>
            <th scope="col">Checks</th>
            <th scope="col">Uptime</th>
            <th scope="col">Latencia media</th>
            {granularity === 'daily' && <th scope="col">Downtime</th>}
          </tr>
        </thead>
        <tbody>
          {[...items].reverse().map((item) => (
            <tr key={item.at} className="history-table__row">
              <td className="history-table__time">{formatTimestamp(item.at, granularity)}</td>
              <td className="history-table__mono">{item.total_checks}</td>
              <td className="history-table__mono">{item.uptime_percent.toFixed(1)}%</td>
              <td className="history-table__mono">
                {item.avg_latency_ms != null ? `${item.avg_latency_ms.toFixed(0)} ms` : '—'}
              </td>
              {granularity === 'daily' && (
                <td className="history-table__mono">{item.downtime_minutes ?? 0} min</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
