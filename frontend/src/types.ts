export type MonitorType = 'http' | 'tcp' | 'ping' | 'postgres' | 'redis'

export type MonitorStatus = 'up' | 'down' | 'degraded' | 'unknown'

export interface Monitor {
  id: number
  name: string
  type: MonitorType
  target: string
  interval_seconds: number
  enabled: boolean
  status: MonitorStatus
  last_checked_at: string | null
  response_time_ms: number | null
}

export interface MonitorSummary {
  total: number
  up: number
  down: number
  degraded: number
  unknown: number
}

export interface DashboardStats {
  monitors: MonitorSummary
  uptime_24h_percent: number | null
}
