import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchIncidents } from '../api/client'
import type { Incident, IncidentStatus } from '../types'
import { formatDateTime, formatDuration } from '../utils/time'

type StatusFilter = 'all' | IncidentStatus

const FILTER_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'Todos' },
  { value: 'open', label: 'Activos' },
  { value: 'resolved', label: 'Resueltos' },
]

const REFRESH_INTERVAL_MS = 30_000

export function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [filter, setFilter] = useState<StatusFilter>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (initial = false) => {
    if (initial) setLoading(true)
    try {
      const data = await fetchIncidents({ days: 30 })
      setIncidents(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar incidentes')
    } finally {
      if (initial) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load(true)
    const timer = setInterval(() => void load(false), REFRESH_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [load])

  const visibleIncidents = useMemo(() => {
    if (filter === 'all') return incidents
    return incidents.filter((incident) => incident.status === filter)
  }, [filter, incidents])

  const openCount = useMemo(
    () => incidents.filter((incident) => incident.status === 'open').length,
    [incidents],
  )

  return (
    <div className="incidents-page">
      <header className="main__header">
        <div>
          <p className="main__eyebrow">operaciones</p>
          <h1 className="main__title">Incidentes</h1>
        </div>
        <p className="incidents-page__summary">
          {openCount > 0 ? `${openCount} activo${openCount > 1 ? 's' : ''}` : 'Sin incidentes activos'}
        </p>
      </header>

      <main className="main__content">
        <div className="history-range" role="group" aria-label="Filtrar por estado">
          {FILTER_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`history-range__btn${filter === option.value ? ' history-range__btn--active' : ''}`}
              onClick={() => setFilter(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>

        {loading && <p className="history-loading">Cargando incidentes…</p>}

        {error && (
          <p className="notice notice--error" role="alert">
            <span className="notice__prefix">ERR</span>
            {error}
          </p>
        )}

        {!loading && !error && visibleIncidents.length === 0 && (
          <p className="notice">
            <span className="notice__prefix">INFO</span>
            No hay incidentes en los últimos 30 días.
          </p>
        )}

        {!loading && !error && visibleIncidents.length > 0 && (
          <div className="history-table-wrap">
            <table className="history-table incidents-table">
              <thead>
                <tr>
                  <th scope="col">Estado</th>
                  <th scope="col">Monitor</th>
                  <th scope="col">Inicio</th>
                  <th scope="col">Duración</th>
                  <th scope="col">Checks</th>
                  <th scope="col">Causa</th>
                </tr>
              </thead>
              <tbody>
                {visibleIncidents.map((incident) => (
                  <tr
                    key={incident.id}
                    className={`history-table__row history-table__row--${incident.status === 'open' ? 'down' : 'up'}`}
                  >
                    <td>
                      <span
                        className={`incidents-table__status incidents-table__status--${incident.status}`}
                      >
                        {incident.status === 'open' ? 'Activo' : 'Resuelto'}
                      </span>
                    </td>
                    <td>
                      <Link to={`/incidents/${incident.id}`} className="incidents-table__link">
                        {incident.monitor_name}
                      </Link>
                      <span className="incidents-table__target">{incident.monitor_target}</span>
                    </td>
                    <td className="history-table__time">{formatDateTime(incident.started_at)}</td>
                    <td className="history-table__mono">
                      {formatDuration(incident.started_at, incident.ended_at)}
                    </td>
                    <td className="history-table__mono">{incident.failed_check_count}</td>
                    <td className="history-table__error" title={incident.error_message ?? undefined}>
                      {incident.error_message ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}
