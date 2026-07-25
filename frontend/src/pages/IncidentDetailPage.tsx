import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, fetchIncident } from '../api/client'
import { CheckHistoryTable } from '../components/CheckHistoryTable'
import type { IncidentDetail } from '../types'
import { formatDateTime, formatDuration } from '../utils/time'

export function IncidentDetailPage() {
  const { id } = useParams()
  const incidentId = parseIncidentId(id)

  const [incident, setIncident] = useState<IncidentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (incidentId === null) {
      setError('ID de incidente inválido')
      setLoading(false)
      return
    }

    try {
      const data = await fetchIncident(incidentId)
      setIncident(data)
      setError(null)
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setError('Incidente no encontrado')
      } else {
        setError(err instanceof Error ? err.message : 'Error al cargar el incidente')
      }
      setIncident(null)
    } finally {
      setLoading(false)
    }
  }, [incidentId])

  useEffect(() => {
    void load()
  }, [load])

  if (incidentId === null) {
    return (
      <div className="detail">
        <p className="notice notice--error" role="alert">
          <span className="notice__prefix">ERR</span>
          ID de incidente inválido
        </p>
        <Link to="/incidents" className="detail__back">
          ← Volver a incidentes
        </Link>
      </div>
    )
  }

  return (
    <div className="detail">
      <Link to="/incidents" className="detail__back">
        ← Incidentes
      </Link>

      {loading && <p className="history-loading">Cargando incidente…</p>}

      {error && (
        <p className="notice notice--error" role="alert">
          <span className="notice__prefix">ERR</span>
          {error}
        </p>
      )}

      {incident && (
        <>
          <header className="detail__header">
            <div className="detail__title-row">
              <span
                className={`incidents-table__status incidents-table__status--${incident.status}`}
              >
                {incident.status === 'open' ? 'Activo' : 'Resuelto'}
              </span>
              <div>
                <h1 className="detail__title">{incident.monitor_name}</h1>
                <p className="detail__target">{incident.monitor_target}</p>
              </div>
            </div>

            <dl className="detail__meta">
              <div>
                <dt>Inicio</dt>
                <dd>{formatDateTime(incident.started_at)}</dd>
              </div>
              <div>
                <dt>Fin</dt>
                <dd>{incident.ended_at ? formatDateTime(incident.ended_at) : '—'}</dd>
              </div>
              <div>
                <dt>Duración</dt>
                <dd>{formatDuration(incident.started_at, incident.ended_at)}</dd>
              </div>
              <div>
                <dt>Checks fallidos</dt>
                <dd>{incident.failed_check_count}</dd>
              </div>
              <div>
                <dt>Monitor</dt>
                <dd>
                  <Link to={`/monitors/${incident.monitor_id}`}>Ver monitor</Link>
                </dd>
              </div>
            </dl>

            {incident.error_message && (
              <p className="incidents-detail__error">
                <span className="notice__prefix">ERR</span>
                {incident.error_message}
              </p>
            )}
          </header>

          <section className="detail__section">
            <div className="section-header">
              <h2 className="section-header__title">Checks durante el incidente</h2>
              <span className="section-header__count">{incident.checks.length} registros</span>
            </div>
            <CheckHistoryTable items={incident.checks} />
          </section>
        </>
      )}
    </div>
  )
}

function parseIncidentId(raw: string | undefined): number | null {
  if (!raw || !/^\d+$/.test(raw)) return null
  const id = Number(raw)
  if (!Number.isSafeInteger(id) || id < 1) return null
  return id
}
