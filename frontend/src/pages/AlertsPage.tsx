import { useCallback, useEffect, useState } from 'react'
import {
  ApiError,
  createAlertRecipient,
  deleteAlertRecipient,
  fetchAlertRecipients,
  fetchAlertSettings,
  updateAlertRecipient,
  updateAlertSettings,
} from '../api/client'
import type { AlertRecipient, AlertSettings } from '../types'

export function AlertsPage() {
  const [settings, setSettings] = useState<AlertSettings | null>(null)
  const [recipients, setRecipients] = useState<AlertRecipient[]>([])
  const [cooldown, setCooldown] = useState(15)
  const [alertOnDown, setAlertOnDown] = useState(true)
  const [alertOnRecovery, setAlertOnRecovery] = useState(false)
  const [statusPagePublic, setStatusPagePublic] = useState(true)
  const [newEmail, setNewEmail] = useState('')
  const [loading, setLoading] = useState(true)
  const [savingSettings, setSavingSettings] = useState(false)
  const [addingRecipient, setAddingRecipient] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [alertSettings, recipientList] = await Promise.all([
        fetchAlertSettings(),
        fetchAlertRecipients(),
      ])
      setSettings(alertSettings)
      setCooldown(alertSettings.down_alert_cooldown_minutes)
      setAlertOnDown(alertSettings.alert_on_down)
      setAlertOnRecovery(alertSettings.alert_on_recovery)
      setStatusPagePublic(alertSettings.status_page_public)
      setRecipients(recipientList)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar alertas')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleSaveSettings(event: React.FormEvent) {
    event.preventDefault()
    setSavingSettings(true)
    setNotice(null)
    try {
      const updated = await updateAlertSettings({
        down_alert_cooldown_minutes: cooldown,
        alert_on_down: alertOnDown,
        alert_on_recovery: alertOnRecovery,
        status_page_public: statusPagePublic,
      })
      setSettings(updated)
      setNotice('Ajustes guardados')
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron guardar los ajustes')
    } finally {
      setSavingSettings(false)
    }
  }

  async function handleAddRecipient(event: React.FormEvent) {
    event.preventDefault()
    if (!newEmail.trim()) return
    setAddingRecipient(true)
    setNotice(null)
    try {
      const created = await createAlertRecipient(newEmail.trim())
      setRecipients((prev) => [...prev, created].sort((a, b) => a.email.localeCompare(b.email)))
      setNewEmail('')
      setNotice('Destinatario añadido')
      setError(null)
      await load()
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setError('Email no válido')
      } else {
        setError(err instanceof Error ? err.message : 'No se pudo añadir el destinatario')
      }
    } finally {
      setAddingRecipient(false)
    }
  }

  async function handleToggleRecipient(recipient: AlertRecipient) {
    try {
      const updated = await updateAlertRecipient(recipient.id, !recipient.enabled)
      setRecipients((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo actualizar el destinatario')
    }
  }

  async function handleDeleteRecipient(recipient: AlertRecipient) {
    if (!window.confirm(`¿Eliminar ${recipient.email} de la lista de alertas?`)) return
    try {
      await deleteAlertRecipient(recipient.id)
      setRecipients((prev) => prev.filter((r) => r.id !== recipient.id))
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo eliminar el destinatario')
    }
  }

  return (
    <div className="alerts-page">
      <header className="main__header">
        <div>
          <p className="main__eyebrow">cuenta</p>
          <h1 className="main__title">Alertas</h1>
        </div>
      </header>

      <main className="main__content alerts-page__content">
        {loading && <p className="history-loading">Cargando ajustes…</p>}

        {error && (
          <p className="notice notice--error" role="alert">
            <span className="notice__prefix">ERR</span>
            {error}
          </p>
        )}

        {notice && (
          <p className="notice" role="status">
            <span className="notice__prefix">OK</span>
            {notice}
          </p>
        )}

        {settings && !loading && (
          <>
            <section className="alerts-card">
              <h2 className="alerts-card__title">Estado del envío</h2>
              <dl className="alerts-status">
                <div>
                  <dt>SMTP</dt>
                  <dd className={settings.smtp_configured ? 'alerts-status__ok' : 'alerts-status__warn'}>
                    {settings.smtp_configured ? 'Configurado' : 'Sin configurar (.env)'}
                  </dd>
                </div>
                <div>
                  <dt>Alertas</dt>
                  <dd className={settings.alerts_enabled ? 'alerts-status__ok' : 'alerts-status__warn'}>
                    {settings.alerts_enabled ? 'Activadas' : 'Desactivadas (ALERTS_ENABLED=false)'}
                  </dd>
                </div>
                <div>
                  <dt>Destinatarios activos</dt>
                  <dd>{settings.recipient_count}</dd>
                </div>
              </dl>
              <p className="alerts-card__hint">
                Configura <code>SMTP_*</code> y <code>ALERTS_ENABLED=true</code> en{' '}
                <code>backend/.env</code> para habilitar el envío real.
              </p>
            </section>

            <section className="alerts-card">
              <h2 className="alerts-card__title">Página de estado</h2>
              <p className="alerts-card__hint">
                La status page pública está en <code>/status</code>. Cada monitor puede marcarse
                individualmente como visible o privado al crearlo o editarlo.
              </p>
              <form className="alerts-form" onSubmit={(e) => void handleSaveSettings(e)}>
                <label className="alerts-form__checkbox">
                  <input
                    type="checkbox"
                    checked={statusPagePublic}
                    onChange={(e) => setStatusPagePublic(e.target.checked)}
                  />
                  <span>
                    <strong>Página pública</strong> — cualquiera con el enlace puede ver el estado
                  </span>
                </label>
                {!statusPagePublic && (
                  <p className="alerts-card__hint">
                    Con esta opción desactivada, <code>/status</code> no mostrará información.
                  </p>
                )}
                <button type="submit" className="btn btn--primary" disabled={savingSettings}>
                  {savingSettings ? 'Guardando…' : 'Guardar ajustes'}
                </button>
              </form>
            </section>

            <section className="alerts-card">
              <h2 className="alerts-card__title">Cuándo avisar</h2>
              <form className="alerts-form" onSubmit={(e) => void handleSaveSettings(e)}>
                <label className="alerts-form__checkbox">
                  <input
                    type="checkbox"
                    checked={alertOnDown}
                    onChange={(e) => setAlertOnDown(e.target.checked)}
                  />
                  <span>
                    <strong>Caída del servicio</strong> — cuando un monitor pasa de UP a DOWN
                  </span>
                </label>

                <label className="alerts-form__checkbox">
                  <input
                    type="checkbox"
                    checked={alertOnRecovery}
                    onChange={(e) => setAlertOnRecovery(e.target.checked)}
                  />
                  <span>
                    <strong>Recuperación</strong> — cuando un monitor vuelve a UP tras estar DOWN
                  </span>
                </label>

                <label className="monitor-form__field">
                  <span>Cooldown entre alertas de caída (minutos)</span>
                  <input
                    type="number"
                    min={1}
                    max={1440}
                    value={cooldown}
                    onChange={(e) => setCooldown(Number(e.target.value))}
                  />
                  <span className="alerts-card__hint">
                    Evita correos repetidos si un monitor oscila. Se resetea al recuperarse.
                  </span>
                </label>

                <button type="submit" className="btn btn--primary" disabled={savingSettings}>
                  {savingSettings ? 'Guardando…' : 'Guardar ajustes'}
                </button>
              </form>
            </section>

            <section className="alerts-card">
              <h2 className="alerts-card__title">Destinatarios</h2>
              <p className="alerts-card__hint">
                Todos los emails activos recibirán las alertas de la cuenta.
              </p>

              <form className="alerts-recipient-add" onSubmit={(e) => void handleAddRecipient(e)}>
                <input
                  type="email"
                  required
                  placeholder="ops@tuempresa.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                />
                <button type="submit" className="btn btn--primary" disabled={addingRecipient}>
                  {addingRecipient ? 'Añadiendo…' : 'Añadir'}
                </button>
              </form>

              {recipients.length === 0 ? (
                <p className="notice">
                  <span className="notice__prefix">INFO</span>
                  No hay destinatarios configurados.
                </p>
              ) : (
                <ul className="alerts-recipient-list">
                  {recipients.map((recipient) => (
                    <li key={recipient.id} className="alerts-recipient-list__item">
                      <label className="alerts-form__checkbox">
                        <input
                          type="checkbox"
                          checked={recipient.enabled}
                          onChange={() => void handleToggleRecipient(recipient)}
                        />
                        <span className="alerts-recipient-list__email">{recipient.email}</span>
                      </label>
                      <button
                        type="button"
                        className="btn btn--danger btn--small"
                        onClick={() => void handleDeleteRecipient(recipient)}
                      >
                        Eliminar
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  )
}
