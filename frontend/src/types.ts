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

export type HistoryGranularity = 'auto' | 'raw' | 'hourly' | 'daily'

export interface HistoryPoint {
  at: string
  total_checks: number
  up_checks: number
  uptime_percent: number
  avg_latency_ms: number | null
  min_latency_ms?: number | null
  max_latency_ms?: number | null
  downtime_minutes?: number | null
  status?: MonitorStatus | null
  status_code?: number | null
  error_message?: string | null
  id?: number | null
}

export interface MonitorHistoryResponse {
  granularity: HistoryGranularity
  days: number
  points: HistoryPoint[]
  total: number
}

export type HistoryRange = '24h' | '7d' | '30d' | '90d'

export const HISTORY_RANGE_DAYS: Record<HistoryRange, number> = {
  '24h': 1,
  '7d': 7,
  '30d': 30,
  '90d': 90,
}
