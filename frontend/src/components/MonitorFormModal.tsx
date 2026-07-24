import { MonitorForm } from './MonitorForm'
import type { MonitorInput } from '../utils/monitorForm'

interface MonitorFormModalProps {
  title: string
  submitLabel: string
  initial: MonitorInput
  onSubmit: (values: MonitorInput) => Promise<void>
  onClose: () => void
}

export function MonitorFormModal({
  title,
  submitLabel,
  initial,
  onSubmit,
  onClose,
}: MonitorFormModalProps) {
  return (
    <div className="modal" role="presentation" onClick={onClose}>
      <div
        className="modal__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="monitor-form-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="modal__header">
          <h2 id="monitor-form-title" className="modal__title">
            {title}
          </h2>
          <button type="button" className="modal__close" onClick={onClose} aria-label="Cerrar">
            ×
          </button>
        </header>
        <MonitorForm
          initial={initial}
          submitLabel={submitLabel}
          onSubmit={onSubmit}
          onCancel={onClose}
        />
      </div>
    </div>
  )
}
