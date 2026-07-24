import { useState } from 'react'
import { BrowserRouter, Outlet, Route, Routes } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { DashboardPage } from './pages/DashboardPage'
import { MonitorDetailPage } from './pages/MonitorDetailPage'
import './App.css'

function ShellLayout() {
  const [monitorCount, setMonitorCount] = useState(0)

  return (
    <div className="shell">
      <Sidebar monitorCount={monitorCount} />
      <div className="main">
        <Outlet context={{ setMonitorCount }} />
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
          <Route path="/monitors/:id" element={<MonitorDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
