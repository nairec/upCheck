import type { CheckResultBrief, MonitorStatus } from '../types'

interface SparklineProps {
  points: CheckResultBrief[]
  className?: string
}

const STATUS_HEIGHT: Record<MonitorStatus, number> = {
  up: 85,
  degraded: 55,
  down: 20,
  unknown: 40,
}

export function Sparkline({ points, className = '' }: SparklineProps) {
  if (points.length === 0) {
    return (
      <div className={`sparkline sparkline--empty ${className}`} aria-hidden="true">
        {Array.from({ length: 12 }, (_, i) => (
          <span key={i} className="sparkline__bar sparkline__bar--empty" />
        ))}
      </div>
    )
  }

  return (
    <div className={`sparkline ${className}`} aria-hidden="true">
      {points.map((point, index) => (
        <span
          key={`${point.checked_at}-${index}`}
          className={`sparkline__bar sparkline__bar--${point.status}`}
          style={{
            height: `${point.response_time_ms != null ? Math.min(100, 20 + point.response_time_ms / 5) : STATUS_HEIGHT[point.status]}%`,
          }}
        />
      ))}
    </div>
  )
}
