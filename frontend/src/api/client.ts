import type { CheckResultPage, DashboardStats, Monitor } from '../types'

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
      const body = (await response.json()) as { detail?: string }
      if (body.detail) detail = body.detail
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

export function fetchDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>('/monitors/stats')
}
