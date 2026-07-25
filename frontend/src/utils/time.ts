const MINUTE = 60_000
const HOUR = 3_600_000
const DAY = 86_400_000

export function formatRelativeTime(iso: string | null): string {
  if (!iso) return 'sin comprobar'

  const diff = Date.now() - new Date(iso).getTime()
  if (diff < MINUTE) return 'hace <1m'
  if (diff < HOUR) return `hace ${Math.floor(diff / MINUTE)}m`
  if (diff < DAY) return `hace ${Math.floor(diff / HOUR)}h`
  return `hace ${Math.floor(diff / DAY)}d`
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
    timeZoneName: 'short',
  })
}

export function formatDuration(startIso: string, endIso: string | null): string {
  const start = new Date(startIso).getTime()
  const end = endIso ? new Date(endIso).getTime() : Date.now()
  const totalMinutes = Math.max(0, Math.floor((end - start) / MINUTE))

  if (totalMinutes < 1) return '<1 min'
  if (totalMinutes < 60) return `${totalMinutes} min`

  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (hours < 24) return minutes > 0 ? `${hours} h ${minutes} min` : `${hours} h`

  const days = Math.floor(hours / 24)
  const remHours = hours % 24
  return remHours > 0 ? `${days} d ${remHours} h` : `${days} d`
}
