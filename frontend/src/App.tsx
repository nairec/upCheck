import { useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { fetchMonitors } from './api/client'
import { Sidebar } from './components/Sidebar'
import { DashboardPage } from './pages/DashboardPage'
import { AlertsPage } from './pages/AlertsPage'
import { MonitorDetailPage } from './pages/MonitorDetailPage'
import './App.css'

function ShellLayout() {
  const [monitorCount, setMonitorCount] = useState(0)
  const location = useLocation()

  const refreshMonitorCount = useCallback(async () => {
    try {
      const monitors = await fetchMonitors()
      setMonitorCount(monitors.length)
    } catch {
      // Mantener el último valor conocido si la API no responde.
    }
  }, [])

  useEffect(() => {
    void refreshMonitorCount()
  }, [location.pathname, refreshMonitorCount])

  return (
    <div className="shell">
      <Sidebar monitorCount={monitorCount} />
      <div className="main">
        <Outlet context={{ refreshMonitorCount }} />
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<ShellLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/monitors/:id" element={<MonitorDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
