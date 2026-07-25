import type { Monitor, MonitorType } from '../types'

export interface MonitorInput {
  name: string
  type: MonitorType
  target: string
  interval_seconds: number
  timeout_seconds: number
  enabled: boolean
  public_on_status_page: boolean
}

export const SUPPORTED_MONITOR_TYPES: MonitorType[] = ['http', 'tcp']

export const MONITOR_TYPE_LABELS: Record<MonitorType, string> = {
  http: 'HTTP',
  tcp: 'TCP',
  ping: 'Ping (próximamente)',
  postgres: 'PostgreSQL (próximamente)',
  redis: 'Redis (próximamente)',
}

export const DEFAULT_MONITOR_INPUT: MonitorInput = {
  name: '',
  type: 'http',
  target: 'https://',
  interval_seconds: 60,
  timeout_seconds: 10,
  enabled: true,
  public_on_status_page: false,
}

export function monitorToInput(monitor: Monitor): MonitorInput {
  return {
    name: monitor.name,
    type: monitor.type,
    target: monitor.target,
    interval_seconds: monitor.interval_seconds,
    timeout_seconds: monitor.timeout_seconds,
    enabled: monitor.enabled,
    public_on_status_page: monitor.public_on_status_page,
  }
}

export function targetPlaceholder(type: MonitorType): string {
  if (type === 'tcp') return 'host.ejemplo.com:443'
  return 'https://api.ejemplo.com/health'
}

export function targetLabel(type: MonitorType): string {
  return type === 'tcp' ? 'Host:puerto' : 'URL del servicio'
}
