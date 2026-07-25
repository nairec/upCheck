import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchPublicStatus } from '../api/client'
import { HealthBar } from '../components/Sidebar'
import { StatsBar } from '../components/StatsBar'
import { StatusBadge } from '../components/StatusBadge'
import type { DashboardStats, OverallStatus, PublicStatus } from '../types'
import { formatDateTime, formatDuration, formatRelativeTime } from '../utils/time'

const REFRESH_INTERVAL_MS = 30_000

const STATUS_LABELS: Record<OverallStatus, string> = {
  operational: 'Todos los sistemas operativos',
  degraded: 'Rendimiento degradado',
  major_outage: 'Interrupción del servicio',
}

const STATUS_HINTS: Record<OverallStatus, string> = {
  operational: 'Todos los servicios monitorizados responden con normalidad.',
  degraded: 'Algunos servicios presentan latencia o respuestas anómalas.',
  major_outage: 'Hay servicios caídos en este momento.',
}

export function StatusPage() {
  const [status, setStatus] = useState<PublicStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (initial = false) => {
    if (initial) setLoading(true)
    try {
      const data = await fetchPublicStatus()
      setStatus(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el estado')
    } finally {
      if (initial) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load(true)
    const timer = setInterval(() => void load(), REFRESH_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [load])

  const dashboardStats: DashboardStats | null = status
    ? {
        monitors: status.monitors,
        uptime_24h_percent: status.uptime_24h_percent,
      }
    : null

  return (
    <div className="status-page">
      <header className="status-page__header">
        <div className="status-page__brand">
          <span className="status-page__mark" aria-hidden="true">
            ◈
          </span>
          <div>
            <p className="status-page__title">upCheck</p>
            <p className="status-page__subtitle">Estado del servicio</p>
          </div>
        </div>
        <Link to="/" className="status-page__admin-link">
          Panel de control
        </Link>
      </header>

      <main className="status-page__main">
        {loading && !status && (
          <div className="status-page__loading" aria-label="Cargando estado">
            <div className="skeleton-card status-page__skeleton" />
            <div className="skeleton-card status-page__skeleton" />
          </div>
        )}

        {error && (
          <div className="notice notice--error" role="alert">
            <span className="notice__prefix">!</span>
            {error}
          </div>
        )}

        {status && (
          <>
            <section
              className={`status-hero status-hero--${status.status}`}
              aria-label="Estado general"
            >
              <p className="status-hero__eyebrow">estado actual</p>
              <h1 className="status-hero__title">{STATUS_LABELS[status.status]}</h1>
              <p className="status-hero__hint">{STATUS_HINTS[status.status]}</p>
            </section>

            {dashboardStats && (
              <>
                <HealthBar stats={dashboardStats} />
                <StatsBar stats={dashboardStats} />
              </>
            )}

            <section className="status-page__section" aria-labelledby="services-heading">
              <div className="section-header">
                <h2 id="services-heading" className="section-header__title">
                  Servicios
                </h2>
                <p className="section-header__meta">
                  {status.services.length} monitor{status.services.length === 1 ? '' : 'es'} público
                  {status.services.length === 1 ? '' : 's'}
                </p>
              </div>

              {status.services.length === 0 ? (
                <p className="status-page__empty">No hay servicios monitorizados.</p>
              ) : (
                <div className="status-page__table-wrap">
                  <table className="history-table status-page__table">
                    <thead>
                      <tr>
                        <th scope="col">Servicio</th>
                        <th scope="col">Estado</th>
                        <th scope="col">Uptime 24h</th>
                        <th scope="col">Latencia</th>
                        <th scope="col">Último check</th>
                      </tr>
                    </thead>
                    <tbody>
                      {status.services.map((service) => (
                        <tr key={service.id}>
                          <td>
                            <span className="status-page__service-name">{service.name}</span>
                            <span className="status-page__service-type">{service.type}</span>
                          </td>
                          <td>
                            <StatusBadge status={service.status} />
                          </td>
                          <td>
                            {service.uptime_24h_percent != null
                              ? `${service.uptime_24h_percent.toFixed(1)}%`
                              : '—'}
                          </td>
                          <td>
                            {service.response_time_ms != null
                              ? `${Math.round(service.response_time_ms)} ms`
                              : '—'}
                          </td>
                          <td>{formatRelativeTime(service.last_checked_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            {status.open_incidents.length > 0 && (
              <section className="status-page__section" aria-labelledby="incidents-heading">
                <div className="section-header">
                  <h2 id="incidents-heading" className="section-header__title">
                    Incidentes activos
                  </h2>
                </div>
                <div className="status-page__table-wrap">
                  <table className="history-table status-page__table">
                    <thead>
                      <tr>
                        <th scope="col">Servicio</th>
                        <th scope="col">Desde</th>
                        <th scope="col">Duración</th>
                        <th scope="col">Detalle</th>
                      </tr>
                    </thead>
                    <tbody>
                      {status.open_incidents.map((incident) => (
                        <tr key={incident.id}>
                          <td>{incident.monitor_name}</td>
                          <td>{formatDateTime(incident.started_at)}</td>
                          <td>{formatDuration(incident.started_at, null)}</td>
                          <td>{incident.error_message ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </>
        )}
      </main>

      {status && (
        <footer className="status-page__footer">
          <span>Actualizado {formatDateTime(status.updated_at)}</span>
          <span>Se refresca cada 30 s</span>
        </footer>
      )}
    </div>
  )
}
