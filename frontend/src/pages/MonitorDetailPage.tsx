import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import { ApiError, deleteMonitor, fetchMonitor, fetchMonitorHistory, fetchMonitors, updateMonitor } from '../api/client'
import { AggregateHistoryTable } from '../components/AggregateHistoryTable'
import { CheckHistoryTable } from '../components/CheckHistoryTable'
import { MonitorFormModal } from '../components/MonitorFormModal'
import { Sparkline } from '../components/Sparkline'
import { StatusBadge } from '../components/StatusBadge'
import type { ShellContext } from '../context/shell'
import type { CheckResult, HistoryPoint, HistoryRange, Monitor } from '../types'
import { HISTORY_RANGE_DAYS } from '../types'
import { monitorToInput } from '../utils/monitorForm'
import { formatMonitorIndex, monitorDisplayIndex } from '../utils/monitors'
import { formatRelativeTime } from '../utils/time'

const RANGE_OPTIONS: { value: HistoryRange; label: string }[] = [
  { value: '24h', label: '24 h' },
  { value: '7d', label: '7 días' },
  { value: '30d', label: '30 días' },
  { value: '90d', label: '90 días' },
]

export function MonitorDetailPage() {
  const navigate = useNavigate()
  const { refreshSidebar } = useOutletContext<ShellContext>()
  const { id } = useParams()
  const monitorId = parseMonitorId(id)

  const [monitor, setMonitor] = useState<Monitor | null>(null)
  const [displayIndex, setDisplayIndex] = useState<number | null>(null)
  const [range, setRange] = useState<HistoryRange>('7d')
  const [historyPoints, setHistoryPoints] = useState<HistoryPoint[]>([])
  const [historyGranularity, setHistoryGranularity] = useState<'raw' | 'hourly' | 'daily'>('raw')
  const [historyTotal, setHistoryTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [monitorError, setMonitorError] = useState<string | null>(null)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const loadMonitor = useCallback(async () => {
    if (monitorId === null) {
      setMonitorError('ID de monitor inválido')
      setLoading(false)
      return
    }

    try {
      const [data, monitors] = await Promise.all([fetchMonitor(monitorId), fetchMonitors()])
      setMonitor(data)
      setDisplayIndex(monitorDisplayIndex(monitors, monitorId))
      setMonitorError(null)
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setMonitorError('Monitor no encontrado')
      } else {
        setMonitorError(err instanceof Error ? err.message : 'Error desconocido')
      }
      setMonitor(null)
    }
  }, [monitorId])

  const loadHistory = useCallback(async () => {
    if (monitorId === null) return

    setLoading(true)
    try {
      const days = HISTORY_RANGE_DAYS[range]
      const history = await fetchMonitorHistory(monitorId, { days, granularity: 'auto' })
      setHistoryPoints(history.points)
      setHistoryGranularity(
        history.granularity === 'auto' ? 'raw' : history.granularity,
      )
      setHistoryTotal(history.total)
      setHistoryError(null)
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setHistoryError('Monitor no encontrado')
      } else {
        setHistoryError(err instanceof Error ? err.message : 'Error al cargar historial')
      }
    } finally {
      setLoading(false)
    }
  }, [monitorId, range])

  useEffect(() => {
    void loadMonitor()
  }, [loadMonitor])

  useEffect(() => {
    void loadHistory()
  }, [loadHistory])

  async function handleUpdate(values: ReturnType<typeof monitorToInput>) {
    if (monitorId === null) return
    const updated = await updateMonitor(monitorId, values)
    setMonitor(updated)
    setShowEditModal(false)
  }

  async function handleDelete() {
    if (monitorId === null || monitor === null) return
    const confirmed = window.confirm(
      `¿Eliminar el monitor "${monitor.name}"? Se borrará también todo su historial.`,
    )
    if (!confirmed) return

    setDeleting(true)
    try {
      await deleteMonitor(monitorId)
      await refreshSidebar()
      navigate('/')
    } catch (err) {
      setMonitorError(err instanceof Error ? err.message : 'No se pudo eliminar el monitor')
      setDeleting(false)
    }
  }

  if (monitorId === null) {
    return (
      <div className="detail">
        <p className="notice notice--error" role="alert">
          <span className="notice__prefix">ERR</span>
          ID de monitor inválido
        </p>
        <Link to="/" className="detail__back">
          ← Volver al panel
        </Link>
      </div>
    )
  }

  const sparklinePoints = historyPoints.map(historyPointToSparkline)
  const rawChecks =
    historyGranularity === 'raw' && monitor
      ? [...historyPoints]
          .reverse()
          .map((point) => historyPointToCheckResult(point, monitor.id))
      : []

  return (
    <div className="detail">
      <Link to="/" className="detail__back">
        ← Panel de control
      </Link>

      {monitorError && (
        <p className="notice notice--error" role="alert">
          <span className="notice__prefix">ERR</span>
          {monitorError}
        </p>
      )}

      {monitor && (
        <>
          <header className="detail__header">
            <div className="detail__title-row">
              <span className="detail__index">
                {displayIndex != null ? formatMonitorIndex(displayIndex) : '—'}
              </span>
              <div>
                <h1 className="detail__title">{monitor.name}</h1>
                <p className="detail__target">{monitor.target}</p>
              </div>
              <StatusBadge status={monitor.status} />
            </div>

            <div className="detail__actions">
              <button type="button" className="btn btn--ghost" onClick={() => setShowEditModal(true)}>
                Editar
              </button>
              <button
                type="button"
                className="btn btn--danger"
                disabled={deleting}
                onClick={() => void handleDelete()}
              >
                {deleting ? 'Eliminando…' : 'Eliminar'}
              </button>
            </div>

            <dl className="detail__meta">
              <div>
                <dt>Tipo</dt>
                <dd>{monitor.type.toUpperCase()}</dd>
              </div>
              <div>
                <dt>Intervalo</dt>
                <dd>{monitor.interval_seconds}s</dd>
              </div>
              <div>
                <dt>Timeout</dt>
                <dd>{monitor.timeout_seconds}s</dd>
              </div>
              <div>
                <dt>Último check</dt>
                <dd>{formatRelativeTime(monitor.last_checked_at)}</dd>
              </div>
              <div>
                <dt>Latencia</dt>
                <dd>
                  {monitor.response_time_ms != null
                    ? `${monitor.response_time_ms.toFixed(0)} ms`
                    : '—'}
                </dd>
              </div>
            </dl>
          </header>

          <section className="detail__section">
            <div className="section-header">
              <h2 className="section-header__title">Tendencia</h2>
              <div className="history-range" role="group" aria-label="Rango temporal">
                {RANGE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    className={`history-range__btn${range === option.value ? ' history-range__btn--active' : ''}`}
                    onClick={() => setRange(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
            <Sparkline points={sparklinePoints} className="detail__sparkline" />
          </section>

          <section className="detail__section">
            <div className="section-header">
              <h2 className="section-header__title">Historial de checks</h2>
              <span className="section-header__count">
                {historyTotal} registros
                {historyGranularity !== 'raw' ? ` (${historyGranularity})` : ''}
              </span>
            </div>

            {historyGranularity === 'raw' ? (
              <CheckHistoryTable items={rawChecks} loading={loading && rawChecks.length === 0} />
            ) : (
              <AggregateHistoryTable
                items={historyPoints}
                granularity={historyGranularity}
                loading={loading && historyPoints.length === 0}
              />
            )}

            {historyError && (
              <p className="notice notice--error" role="alert">
                <span className="notice__prefix">ERR</span>
                {historyError}
              </p>
            )}
          </section>
        </>
      )}

      {monitor && showEditModal && (
        <MonitorFormModal
          title="Editar monitor"
          submitLabel="Guardar cambios"
          initial={monitorToInput(monitor)}
          onSubmit={handleUpdate}
          onClose={() => setShowEditModal(false)}
        />
      )}
    </div>
  )
}

function parseMonitorId(raw: string | undefined): number | null {
  if (!raw || !/^\d+$/.test(raw)) return null
  const id = Number(raw)
  if (!Number.isSafeInteger(id) || id < 1) return null
  return id
}

function historyPointToSparkline(point: HistoryPoint) {
  const status =
    point.status ??
    (point.uptime_percent >= 99 ? 'up' : point.uptime_percent <= 50 ? 'down' : 'degraded')
  return {
    status,
    response_time_ms: point.avg_latency_ms,
    checked_at: point.at,
  }
}

function historyPointToCheckResult(point: HistoryPoint, monitorId: number): CheckResult {
  return {
    id: point.id ?? 0,
    monitor_id: monitorId,
    status: point.status ?? 'unknown',
    response_time_ms: point.avg_latency_ms,
    status_code: point.status_code ?? null,
    error_message: point.error_message ?? null,
    checked_at: point.at,
  }
}
