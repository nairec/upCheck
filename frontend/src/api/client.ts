import type { DashboardStats, Monitor } from '../types'

const API_BASE = '/api/v1'

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

export function fetchMonitors(): Promise<Monitor[]> {
  return request<Monitor[]>('/monitors')
}

export function fetchDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>('/monitors/stats')
}
