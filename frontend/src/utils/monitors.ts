import type { Monitor } from '../types'

/** Orden estable para numeración visual (01, 02…) independiente del id en BD. */
export function sortMonitors(monitors: Monitor[]): Monitor[] {
  return [...monitors].sort((a, b) => a.id - b.id)
}

export function formatMonitorIndex(index: number): string {
  return String(index).padStart(2, '0')
}

export function monitorDisplayIndex(monitors: Monitor[], monitorId: number): number | null {
  const position = sortMonitors(monitors).findIndex((monitor) => monitor.id === monitorId)
  return position >= 0 ? position + 1 : null
}
