import { useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { fetchIncidents, fetchMonitors } from './api/client'
import { Sidebar } from './components/Sidebar'
import { DashboardPage } from './pages/DashboardPage'
import { AlertsPage } from './pages/AlertsPage'
import { IncidentDetailPage } from './pages/IncidentDetailPage'
import { IncidentsPage } from './pages/IncidentsPage'
import { MonitorDetailPage } from './pages/MonitorDetailPage'
import { StatusPage } from './pages/StatusPage'
import './App.css'

const SIDEBAR_REFRESH_MS = 30_000

function ShellLayout() {
  const [monitorCount, setMonitorCount] = useState(0)
  const [openIncidentCount, setOpenIncidentCount] = useState(0)
  const location = useLocation()

  const refreshSidebar = useCallback(async () => {
    try {
      const [monitors, openIncidents] = await Promise.all([
        fetchMonitors(),
        fetchIncidents({ status: 'open', days: 30 }),
      ])
      setMonitorCount(monitors.length)
      setOpenIncidentCount(openIncidents.length)
    } catch {
      // Mantener el último valor conocido si la API no responde.
    }
  }, [])

  useEffect(() => {
    void refreshSidebar()
    const timer = setInterval(() => void refreshSidebar(), SIDEBAR_REFRESH_MS)
    return () => clearInterval(timer)
  }, [location.pathname, refreshSidebar])

  return (
    <div className="shell">
      <Sidebar monitorCount={monitorCount} openIncidentCount={openIncidentCount} />
      <div className="main">
        <Outlet context={{ refreshSidebar }} />
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/status" element={<StatusPage />} />
        <Route element={<ShellLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/incidents/:id" element={<IncidentDetailPage />} />
          <Route path="/monitors/:id" element={<MonitorDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
