import { useEffect, useState } from 'react'
import type { MonitorInput } from '../utils/monitorForm'
import {
  DEFAULT_MONITOR_INPUT,
  MONITOR_TYPE_LABELS,
  SUPPORTED_MONITOR_TYPES,
  targetLabel,
  targetPlaceholder,
} from '../utils/monitorForm'

interface MonitorFormProps {
  initial: MonitorInput
  submitLabel: string
  onSubmit: (values: MonitorInput) => Promise<void>
  onCancel: () => void
}

export function MonitorForm({ initial, submitLabel, onSubmit, onCancel }: MonitorFormProps) {
  const [values, setValues] = useState<MonitorInput>(initial)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setValues(initial)
    setError(null)
  }, [initial])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onSubmit(values)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el monitor')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="monitor-form" onSubmit={(event) => void handleSubmit(event)}>
      <label className="monitor-form__field">
        <span>Nombre</span>
        <input
          type="text"
          required
          maxLength={120}
          value={values.name}
          onChange={(event) => setValues((prev) => ({ ...prev, name: event.target.value }))}
          placeholder="API producción"
        />
      </label>

      <label className="monitor-form__field">
        <span>Tipo de conexión</span>
        <select
          value={values.type}
          onChange={(event) => {
            const type = event.target.value as MonitorInput['type']
            setValues((prev) => ({
              ...prev,
              type,
              target: type === 'tcp' ? '' : prev.target.startsWith('http') ? prev.target : 'https://',
            }))
          }}
        >
          {SUPPORTED_MONITOR_TYPES.map((type) => (
            <option key={type} value={type}>
              {MONITOR_TYPE_LABELS[type]}
            </option>
          ))}
        </select>
      </label>

      <label className="monitor-form__field">
        <span>{targetLabel(values.type)}</span>
        <input
          type="text"
          required
          maxLength={500}
          value={values.target}
          onChange={(event) => setValues((prev) => ({ ...prev, target: event.target.value }))}
          placeholder={targetPlaceholder(values.type)}
        />
      </label>

      <div className="monitor-form__row">
        <label className="monitor-form__field">
          <span>Intervalo (s)</span>
          <input
            type="number"
            required
            min={30}
            max={3600}
            value={values.interval_seconds}
            onChange={(event) =>
              setValues((prev) => ({ ...prev, interval_seconds: Number(event.target.value) }))
            }
          />
        </label>

        <label className="monitor-form__field">
          <span>Timeout (s)</span>
          <input
            type="number"
            required
            min={1}
            max={300}
            value={values.timeout_seconds}
            onChange={(event) =>
              setValues((prev) => ({ ...prev, timeout_seconds: Number(event.target.value) }))
            }
          />
        </label>
      </div>

      <label className="monitor-form__checkbox">
        <input
          type="checkbox"
          checked={values.enabled}
          onChange={(event) => setValues((prev) => ({ ...prev, enabled: event.target.checked }))}
        />
        <span>Monitor activo</span>
      </label>

      {error && (
        <p className="notice notice--error" role="alert">
          <span className="notice__prefix">ERR</span>
          {error}
        </p>
      )}

      <div className="monitor-form__actions">
        <button type="button" className="monitor-form__btn monitor-form__btn--ghost" onClick={onCancel}>
          Cancelar
        </button>
        <button type="submit" className="monitor-form__btn monitor-form__btn--primary" disabled={saving}>
          {saving ? 'Guardando…' : submitLabel}
        </button>
      </div>
    </form>
  )
}

export { DEFAULT_MONITOR_INPUT }
