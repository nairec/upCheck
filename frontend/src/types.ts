export type MonitorType = 'http' | 'tcp' | 'ping' | 'postgres' | 'redis'

export type MonitorStatus = 'up' | 'down' | 'degraded' | 'unknown'

export interface CheckResultBrief {
  status: MonitorStatus
  response_time_ms: number | null
  checked_at: string
}

export interface CheckResult {
  id: number
  monitor_id: number
  status: MonitorStatus
  response_time_ms: number | null
  status_code: number | null
  error_message: string | null
  checked_at: string
}

export interface CheckResultPage {
  items: CheckResult[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface Monitor {
  id: number
  name: string
  type: MonitorType
  target: string
  interval_seconds: number
  timeout_seconds: number
  enabled: boolean
  status: MonitorStatus
  last_checked_at: string | null
  response_time_ms: number | null
  recent_checks?: CheckResultBrief[]
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
