# Estructura del proyecto

Documento de referencia sobre el propósito de cada archivo, las interacciones entre módulos y las decisiones de diseño.

## Visión general

Monorepo con frontend SPA, API REST, workers de checks y persistencia en PostgreSQL:

```
React SPA ──/api/v1/*──▶ FastAPI ──▶ PostgreSQL
                              ▲
Celery Beat ──▶ Redis ◀── Celery Worker ──▶ ejecuta checks ──▶ PostgreSQL
```

- **FastAPI** usa SQLAlchemy **async** (`asyncpg`) para las peticiones HTTP.
- **Celery workers** usan SQLAlchemy **sync** (`psycopg2`) porque las tareas son síncronas.
- **Redis** actúa como broker y backend de resultados de Celery.
- **Celery Beat** dispara periódicamente `dispatch_due_checks`, que encola checks individuales por monitor.

## Backend (`backend/`)

| Archivo | Propósito |
|---------|-----------|
| `app/models/monitor.py` | Modelo `Monitor`: configuración del check (tipo, target, intervalo, estado cacheado). |
| `app/models/check_result.py` | Modelo `CheckResult`: historial de cada ejecución (status, latencia, error). |
| `app/models/enums.py` | Enums compartidos `MonitorType` y `MonitorStatus` (fuente única de verdad). |
| `app/schemas/monitor.py` | Schemas Pydantic para la API; importan los enums de `models.enums`. |
| `app/services/monitor_service.py` | Lógica sync para Celery: `get_due_monitors`, `claim_monitor_for_check`, `execute_check`, `dashboard_stats`. |
| `app/services/monitor_service_async.py` | Lógica async para FastAPI: list/create/stats. |
| `app/checks/runner.py` | Dispatcher de checks por tipo; implementados HTTP y TCP. |
| `app/checks/http.py` | Check HTTP con `httpx` (status code, latencia, errores). |
| `app/worker/celery_app.py` | Configuración de Celery + beat schedule (`dispatch_interval_seconds`). |
| `app/worker/tasks.py` | Tareas `dispatch_due_checks` y `run_monitor_check`. |
| `app/core/database.py` | Engine async + `get_db()` para FastAPI. |
| `app/core/sync_database.py` | Engine sync para workers Celery. |
| `alembic/` | Migraciones; `001_initial_schema.py` crea tablas y seed de 2 monitores; `002_add_monitor_lease_until.py` añade columna de lease para claims atómicos. |
| `entrypoint.sh` | Ejecuta `alembic upgrade head` antes de arrancar uvicorn. |

## Frontend (`frontend/`)

| Archivo | Propósito |
|---------|-----------|
| `public/fonts/` | Geist Sans y Geist Mono (woff2 variable). |
| `src/fonts.css` | `@font-face` para las fuentes Geist. |
| `src/index.css` | Design tokens Control Room: ámbar, crema, blanco sobre fondo `#0a0908`; textura noise sutil. |
| `src/App.css` | Layout: sidebar, health bar, stats grid, cards con jerarquía de severidad, responsive. |
| `src/App.tsx` | Shell Control Room: sidebar + panel, reloj UTC, skeleton loading, refresh bar. |
| `src/components/Sidebar.tsx` | Navegación lateral + `HealthBar` (uptime 24h; si no hay historial, la barra refleja el % de monitores operativos). |
| `src/components/MonitorCard.tsx` | Card con sparkline, tiempo relativo, estados quiet/critical. |
| `src/components/StatusBadge.tsx` | Dot + label mono (`OK`/`DOWN`/`WARN`). |
| `src/utils/time.ts` | `formatRelativeTime()` para contexto temporal en cards. |

## Raíz

| Archivo | Propósito |
|---------|-----------|
| `docker-compose.yml` | Postgres + Redis + backend + celery-worker + celery-beat + frontend. |
| `Makefile` | Atajos incluyendo `worker` y `beat` para desarrollo local. |

## Decisiones de diseño

1. **Doble capa de acceso a datos (async/sync)** — FastAPI no bloquea el event loop; Celery ejecuta checks síncronos (socket, httpx) sin complejidad de async en workers.
2. **Scheduler fan-out con Celery Beat** — Beat corre cada 30 s una tarea `dispatch_due_monitors` que consulta monitores vencidos y encola `run_monitor_check(monitor_id)` por cada uno. Esto permite añadir/eliminar monitores sin reconfigurar schedules.
3. **Estado cacheado en `Monitor`** — `status`, `response_time_ms` y `last_checked_at` se actualizan en cada check para lecturas rápidas del dashboard; `CheckResult` guarda el historial completo. `claim_monitor_for_check` reserva atómicamente un monitor antes de ejecutar el check usando `lease_until` (duración basada en `timeout_seconds`) para evitar ejecuciones concurrentes sin adelantar `last_checked_at`. `execute_check` y `release_monitor_lease` verifican el token de lease (`expected_lease_until`) para no pisar ni liberar reservas de otro worker; el UPDATE de claim también condiciona `last_checked_at` para evitar reclamar tras un check completado por otro worker. Si `execute_check` falla tras añadir un `CheckResult` pendiente, `run_monitor_check` hace `rollback()` antes de `release_monitor_lease`, y `release_monitor_lease` también descarta trabajo no confirmado para que su `commit()` no persista historial huérfano sin actualizar el monitor.
4. **Uptime 24h calculado desde `check_results`** — porcentaje de checks `up` en las últimas 24 h (no mock).
5. **Enums en un solo módulo** — `app/models/enums.py` evita duplicación entre SQLAlchemy, Pydantic y (futuro) Celery serializers.
6. **Estilo Control Room (frontend)** — paleta ámbar/crema/blanco, Geist Sans/Mono, sidebar + health bar, severidad visual (UP atenuado, DOWN con pulso), sin estética genérica de dashboard IA.
