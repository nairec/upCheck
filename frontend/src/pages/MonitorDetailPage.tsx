import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, fetchMonitor, fetchMonitorResults } from '../api/client'
import { CheckHistoryTable } from '../components/CheckHistoryTable'
import { Sparkline } from '../components/Sparkline'
import { StatusBadge } from '../components/StatusBadge'
import type { CheckResult, Monitor } from '../types'
import { formatRelativeTime } from '../utils/time'

const PAGE_SIZE = 50

export function MonitorDetailPage() {
  const { id } = useParams()
  const monitorId = parseMonitorId(id)

  const [monitor, setMonitor] = useState<Monitor | null>(null)
  const [results, setResults] = useState<CheckResult[]>([])
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [monitorError, setMonitorError] = useState<string | null>(null)
  const [historyError, setHistoryError] = useState<string | null>(null)

  const loadMonitor = useCallback(async () => {
    if (monitorId === null) {
      setMonitorError('ID de monitor inválido')
      setLoading(false)
      return
    }

    try {
      const data = await fetchMonitor(monitorId)
      setMonitor(data)
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

  const loadResults = useCallback(
    async (nextOffset: number, append: boolean) => {
      if (monitorId === null) return

      if (append) {
        setLoadingMore(true)
      } else {
        setLoading(true)
      }

      try {
        const page = await fetchMonitorResults(monitorId, {
          limit: PAGE_SIZE,
          offset: nextOffset,
        })
        setResults((prev) => (append ? [...prev, ...page.items] : page.items))
        setTotal(page.total)
        setHasMore(page.has_more)
        setOffset(nextOffset + page.items.length)
        setHistoryError(null)
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setHistoryError('Monitor no encontrado')
        } else {
          setHistoryError(err instanceof Error ? err.message : 'Error al cargar historial')
        }
      } finally {
        setLoading(false)
        setLoadingMore(false)
      }
    },
    [monitorId],
  )

  useEffect(() => {
    void loadMonitor()
    void loadResults(0, false)
  }, [loadMonitor, loadResults])

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
              <span className="detail__index">{String(monitor.id).padStart(2, '0')}</span>
              <div>
                <h1 className="detail__title">{monitor.name}</h1>
                <p className="detail__target">{monitor.target}</p>
              </div>
              <StatusBadge status={monitor.status} />
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
            <h2 className="section-header__title">Tendencia reciente</h2>
            <Sparkline points={results.slice(0, 24).reverse()} className="detail__sparkline" />
          </section>

          <section className="detail__section">
            <div className="section-header">
              <h2 className="section-header__title">Historial de checks</h2>
              <span className="section-header__count">{total} registros</span>
            </div>

            <CheckHistoryTable items={results} loading={loading && results.length === 0} />

            {historyError && (
              <p className="notice notice--error" role="alert">
                <span className="notice__prefix">ERR</span>
                {historyError}
              </p>
            )}

            {hasMore && (
              <button
                type="button"
                className="detail__load-more"
                disabled={loadingMore}
                onClick={() => void loadResults(offset, true)}
              >
                {loadingMore ? 'Cargando…' : 'Cargar más'}
              </button>
            )}
          </section>
        </>
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
