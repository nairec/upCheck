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
