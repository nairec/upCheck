import type {
  AlertRecipient,
  AlertSettings,
  AlertSettingsUpdate,
  CheckResultPage,
  DashboardStats,
  Incident,
  IncidentDetail,
  Monitor,
  MonitorHistoryResponse,
  PublicStatus,
} from '../types'
import type { MonitorInput } from '../utils/monitorForm'

const API_BASE = '/api/v1'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = (await response.json()) as { detail?: string | Array<{ msg: string }> }
      if (typeof body.detail === 'string') {
        detail = body.detail
      } else if (Array.isArray(body.detail) && body.detail.length > 0) {
        detail = body.detail[0]?.msg ?? detail
      }
    } catch {
      // ignore parse errors
    }
    throw new ApiError(detail, response.status)
  }
  return response.json() as Promise<T>
}

export function fetchMonitors(): Promise<Monitor[]> {
  return request<Monitor[]>('/monitors')
}

export function fetchMonitor(id: number): Promise<Monitor> {
  if (!Number.isInteger(id) || id < 1) {
    return Promise.reject(new ApiError('Invalid monitor id', 400))
  }
  return request<Monitor>(`/monitors/${id}`)
}

export function fetchMonitorResults(
  id: number,
  params: { limit?: number; offset?: number } = {},
): Promise<CheckResultPage> {
  if (!Number.isInteger(id) || id < 1) {
    return Promise.reject(new ApiError('Invalid monitor id', 400))
  }
  const limit = params.limit ?? 50
  const offset = params.offset ?? 0
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })
  return request<CheckResultPage>(`/monitors/${id}/results?${query}`)
}

export function fetchMonitorHistory(
  id: number,
  params: { days?: number; granularity?: 'auto' | 'raw' | 'hourly' | 'daily' } = {},
): Promise<MonitorHistoryResponse> {
  if (!Number.isInteger(id) || id < 1) {
    return Promise.reject(new ApiError('Invalid monitor id', 400))
  }
  const query = new URLSearchParams({
    days: String(params.days ?? 7),
    granularity: params.granularity ?? 'auto',
  })
  return request<MonitorHistoryResponse>(`/monitors/${id}/history?${query}`)
}

export function fetchDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>('/monitors/stats')
}

export function createMonitor(payload: MonitorInput): Promise<Monitor> {
  return request<Monitor>('/monitors', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateMonitor(id: number, payload: Partial<MonitorInput>): Promise<Monitor> {
  if (!Number.isInteger(id) || id < 1) {
    return Promise.reject(new ApiError('Invalid monitor id', 400))
  }
  return request<Monitor>(`/monitors/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteMonitor(id: number): Promise<void> {
  if (!Number.isInteger(id) || id < 1) {
    throw new ApiError('Invalid monitor id', 400)
  }
  const response = await fetch(`${API_BASE}/monitors/${id}`, { method: 'DELETE' })
  if (!response.ok && response.status !== 204) {
    let detail = response.statusText
    try {
      const body = (await response.json()) as { detail?: string }
      detail = body.detail ?? detail
    } catch {
      // ignore
    }
    throw new ApiError(detail, response.status)
  }
}

export function fetchAlertSettings(): Promise<AlertSettings> {
  return request<AlertSettings>('/alerts/settings')
}

export function updateAlertSettings(payload: AlertSettingsUpdate): Promise<AlertSettings> {
  return request<AlertSettings>('/alerts/settings', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function fetchAlertRecipients(): Promise<AlertRecipient[]> {
  return request<AlertRecipient[]>('/alerts/recipients')
}

export function createAlertRecipient(email: string): Promise<AlertRecipient> {
  return request<AlertRecipient>('/alerts/recipients', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, enabled: true }),
  })
}

export function updateAlertRecipient(id: number, enabled: boolean): Promise<AlertRecipient> {
  return request<AlertRecipient>(`/alerts/recipients/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  })
}

export async function deleteAlertRecipient(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/alerts/recipients/${id}`, { method: 'DELETE' })
  if (!response.ok && response.status !== 204) {
    let detail = response.statusText
    try {
      const body = (await response.json()) as { detail?: string }
      detail = body.detail ?? detail
    } catch {
      // ignore
    }
    throw new ApiError(detail, response.status)
  }
}

export function fetchIncidents(params: {
  status?: 'open' | 'resolved'
  monitor_id?: number
  days?: number
} = {}): Promise<Incident[]> {
  const query = new URLSearchParams()
  if (params.status) query.set('status', params.status)
  if (params.monitor_id != null) query.set('monitor_id', String(params.monitor_id))
  if (params.days != null) query.set('days', String(params.days))
  const suffix = query.size > 0 ? `?${query}` : ''
  return request<Incident[]>(`/incidents${suffix}`)
}

export function fetchIncident(id: number): Promise<IncidentDetail> {
  if (!Number.isInteger(id) || id < 1) {
    return Promise.reject(new ApiError('Invalid incident id', 400))
  }
  return request<IncidentDetail>(`/incidents/${id}`)
}

export function fetchPublicStatus(): Promise<PublicStatus> {
  return request<PublicStatus>('/status')
}
