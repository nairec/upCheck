import { useCallback, useEffect, useState } from 'react'
import { fetchDashboardStats, fetchMonitors } from './api/client'
import { MonitorCard } from './components/MonitorCard'
import { StatsBar } from './components/StatsBar'
import type { DashboardStats, Monitor } from './types'
import './App.css'

const REFRESH_INTERVAL_MS = 30_000

function App() {
  const [monitors, setMonitors] = useState<Monitor[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const [monitorList, dashboardStats] = await Promise.all([
        fetchMonitors(),
        fetchDashboardStats(),
      ])
      setMonitors(monitorList)
      setStats(dashboardStats)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
    const timer = setInterval(() => void load(), REFRESH_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [load])

  return (
    <div className="layout">
      <header className="topbar">
        <div className="topbar__brand">
          <span className="topbar__logo" aria-hidden="true" />
          <h1>upCheck</h1>
        </div>
        <span className="topbar__subtitle">Monitoreo de infraestructura</span>
      </header>

      <main className="content">
        {loading && <p className="notice">Cargando estado de los monitores…</p>}

        {error && (
          <p className="notice notice--error">
            No se pudo conectar con la API: {error}
          </p>
        )}

        {!loading && !error && stats && (
          <>
            <StatsBar stats={stats} />

            <section className="grid" aria-label="Monitores">
              {monitors.map((monitor) => (
                <MonitorCard key={monitor.id} monitor={monitor} />
              ))}
            </section>

            {monitors.length === 0 && (
              <p className="notice">No hay monitores configurados todavía.</p>
            )}
          </>
        )}
      </main>

      <footer className="footer">
        Actualización automática cada {REFRESH_INTERVAL_MS / 1000}s
      </footer>
    </div>
  )
}

export default App
