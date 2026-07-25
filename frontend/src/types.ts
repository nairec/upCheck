export type IncidentStatus = 'open' | 'resolved'

export interface Incident {
  id: number
  monitor_id: number
  monitor_name: string
  monitor_target: string
  status: IncidentStatus
  started_at: string
  ended_at: string | null
  error_message: string | null
  failed_check_count: number
}

export interface IncidentDetail extends Incident {
  checks: CheckResult[]
}

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

export interface AlertRecipient {
  id: number
  email: string
  enabled: boolean
  created_at: string
}

export interface AlertSettings {
  alerts_enabled: boolean
  smtp_configured: boolean
  down_alert_cooldown_minutes: number
  alert_on_down: boolean
  alert_on_recovery: boolean
  recipient_count: number
}

export interface AlertSettingsUpdate {
  down_alert_cooldown_minutes?: number
  alert_on_down?: boolean
  alert_on_recovery?: boolean
}

export type OverallStatus = 'operational' | 'degraded' | 'major_outage'

export interface StatusMonitorItem {
  id: number
  name: string
  type: MonitorType
  status: MonitorStatus
  uptime_24h_percent: number | null
  response_time_ms: number | null
  last_checked_at: string | null
}

export interface PublicStatusIncident {
  id: number
  monitor_name: string
  status: IncidentStatus
  started_at: string
  error_message: string | null
  failed_check_count: number
}

export interface PublicStatus {
  status: OverallStatus
  uptime_24h_percent: number | null
  monitors: MonitorSummary
  services: StatusMonitorItem[]
  open_incidents: PublicStatusIncident[]
  updated_at: string
}
