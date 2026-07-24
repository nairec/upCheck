import { useCallback, useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { createMonitor, fetchDashboardStats, fetchMonitors } from '../api/client'
import { MonitorCard } from '../components/MonitorCard'
import { MonitorFormModal } from '../components/MonitorFormModal'
import { HealthBar } from '../components/Sidebar'
import { StatsBar } from '../components/StatsBar'
import type { ShellContext } from '../context/shell'
import type { DashboardStats, Monitor } from '../types'
import { DEFAULT_MONITOR_INPUT } from '../utils/monitorForm'

const REFRESH_INTERVAL_MS = 30_000

export function DashboardPage() {
  const { setMonitorCount } = useOutletContext<ShellContext>()
  const [monitors, setMonitors] = useState<Monitor[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)
  const [showCreateModal, setShowCreateModal] = useState(false)

  const load = useCallback(async () => {
    try {
      const [monitorList, dashboardStats] = await Promise.all([
        fetchMonitors(),
        fetchDashboardStats(),
      ])
      setMonitors(monitorList)
      setStats(dashboardStats)
      setMonitorCount(monitorList.length)
      setError(null)
      setRefreshKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }, [setMonitorCount])

  useEffect(() => {
    void load()
    const timer = setInterval(() => void load(), REFRESH_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [load])

  async function handleCreate(values: typeof DEFAULT_MONITOR_INPUT) {
    await createMonitor(values)
    setShowCreateModal(false)
    await load()
  }

  return (
    <>
      <header className="main__header">
        <div>
          <p className="main__eyebrow">infraestructura</p>
          <h1 className="main__title">Panel de control</h1>
        </div>
        <div className="main__header-actions">
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => setShowCreateModal(true)}
          >
            + Añadir monitor
          </button>
          <div className="main__clock" aria-label="Hora del sistema">
            <span className="main__clock-label">UTC</span>
            <Clock />
          </div>
        </div>
      </header>

      <div className="refresh-bar" key={refreshKey} aria-hidden="true" />

      <main className="main__content">
        {loading && (
          <div className="skeleton-grid" aria-label="Cargando monitores">
            {Array.from({ length: 4 }, (_, i) => (
              <div key={i} className="skeleton-card" />
            ))}
          </div>
        )}

        {error && (
          <p className="notice notice--error" role="alert">
            <span className="notice__prefix">ERR</span>
            No se pudo conectar con la API — {error}
          </p>
        )}

        {!loading && !error && stats && (
          <>
            <HealthBar stats={stats} />
            <StatsBar stats={stats} />

            <div className="section-header">
              <h2 className="section-header__title">Monitores</h2>
              <span className="section-header__count">{monitors.length} configurados</span>
            </div>

            <section className="grid" aria-label="Monitores">
              {monitors.map((monitor) => (
                <MonitorCard key={monitor.id} monitor={monitor} />
              ))}
            </section>

            {monitors.length === 0 && (
              <div className="empty-state">
                <p className="notice">
                  <span className="notice__prefix">INFO</span>
                  No hay monitores configurados todavía.
                </p>
                <button
                  type="button"
                  className="btn btn--primary"
                  onClick={() => setShowCreateModal(true)}
                >
                  Crear el primero
                </button>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="main__footer">
        <span>refresh · {REFRESH_INTERVAL_MS / 1000}s</span>
        <span className="main__footer-sep">·</span>
        <span>upCheck control room</span>
      </footer>

      {showCreateModal && (
        <MonitorFormModal
          title="Nuevo monitor"
          submitLabel="Crear monitor"
          initial={DEFAULT_MONITOR_INPUT}
          onSubmit={handleCreate}
          onClose={() => setShowCreateModal(false)}
        />
      )}
    </>
  )
}

function Clock() {
  const [time, setTime] = useState(() => formatUtc())

  useEffect(() => {
    const id = setInterval(() => setTime(formatUtc()), 1000)
    return () => clearInterval(id)
  }, [])

  return <time className="main__clock-time">{time}</time>
}

function formatUtc(): string {
  return new Date().toISOString().slice(11, 19)
}
