# Estructura del proyecto

Documento de referencia sobre el propósito de cada archivo, las interacciones entre módulos y las decisiones de diseño.

## Visión general

Monorepo con dos aplicaciones que se comunican por HTTP (REST):

```
React SPA (frontend/) ──/api/v1/*──▶ FastAPI (backend/) ──▶ PostgreSQL
```

- En **desarrollo**, Vite hace proxy de `/api` al backend (puerto 8000), evitando problemas de CORS.
- En **Docker Compose**, cada servicio corre en su contenedor; la base de datos incluye healthcheck para que el backend arranque solo cuando Postgres está listo.

## Backend (`backend/`)

| Archivo | Propósito |
|---------|-----------|
| `pyproject.toml` | Dependencias y configuración (ruff, pytest). Instalable con `pip install -e ".[dev]"`. |
| `app/main.py` | Factory `create_app()`: crea la app FastAPI, registra CORS, routers y el endpoint `/health`. El `lifespan` queda preparado para inicializar DB y scheduler en fases siguientes. |
| `app/config.py` | Settings con `pydantic-settings`: lee variables de entorno / `.env`. `get_settings()` está cacheado con `lru_cache`. |
| `app/api/router.py` | Router raíz que agrega los routers de módulos bajo `/api/v1`. |
| `app/api/routes/monitors.py` | Endpoints de monitores: `GET /monitors` y `GET /monitors/stats`. **Actualmente devuelve datos mock** hasta implementar la capa de base de datos. |
| `app/api/routes/system.py` | Info del sistema (`/system/info`). |
| `app/schemas/monitor.py` | Schemas Pydantic: `MonitorType`, `MonitorStatus` (enums), `MonitorCreate`, `MonitorRead`, `DashboardStats`. Es el contrato de la API que consume el frontend. |
| `app/core/database.py` | Engine async de SQLAlchemy 2.0 + `get_db()` como dependencia de FastAPI. Aún sin modelos que lo usen. |
| `app/models/` | Reservado para modelos SQLAlchemy (`Monitor`, `CheckResult`, `Incident`). |
| `tests/test_health.py` | Test de humo del endpoint `/health` usando `httpx.ASGITransport` (sin servidor real). |
| `Dockerfile` | Imagen Python 3.12 slim con uvicorn en modo reload (desarrollo). |

## Frontend (`frontend/`)

| Archivo | Propósito |
|---------|-----------|
| `vite.config.ts` | Configuración de Vite con proxy `/api` → backend. `VITE_API_URL` permite apuntar a otro host (usado en Docker). |
| `src/types.ts` | Tipos TypeScript espejo de los schemas Pydantic del backend. Si cambia el contrato de la API, actualizar ambos lados. |
| `src/api/client.ts` | Cliente HTTP mínimo sobre `fetch` con manejo de errores. Funciones: `fetchMonitors()`, `fetchDashboardStats()`. |
| `src/App.tsx` | Página principal del dashboard: carga monitores y stats en paralelo, refresco automático cada 30 s (`setInterval`), estados de carga y error. |
| `src/components/MonitorCard.tsx` | Card de un monitor: nombre, target, tipo, intervalo, latencia y borde de color según estado. |
| `src/components/StatsBar.tsx` | Resumen superior: total, operativos, caídos y uptime 24h. |
| `src/components/StatusBadge.tsx` | Badge de estado (up/down/degraded/unknown) con etiquetas en español. |
| `src/index.css` | Design tokens (variables CSS): paleta dark, tipografías. Tema oscuro fijo. |
| `src/App.css` | Estilos de layout, cards, stats y badges. Responsive vía grid `auto-fill` y media query móvil. |
| `Dockerfile` | Imagen node:22-alpine ejecutando el dev server de Vite. |

## Raíz

| Archivo | Propósito |
|---------|-----------|
| `docker-compose.yml` | Orquesta Postgres 17, backend y frontend con volúmenes para hot-reload en desarrollo. |
| `Makefile` | Atajos: `make backend`, `make frontend`, `make test`, `make lint`, `make up`. |
| `ROADMAP.md` | Fases de desarrollo del producto. |

## Decisiones de diseño

1. **Monorepo con API separada de la SPA** — el backend expone REST documentado (Swagger en `/docs`) y el frontend es un cliente más; facilita añadir después una status page pública u otros consumidores.
2. **Datos mock en la capa de rutas** — la fase de scaffold valida el contrato API↔UI de extremo a extremo sin bloquearse en la base de datos. La sustitución por SQLAlchemy no cambia el contrato (los schemas ya usan `from_attributes`).
3. **CSS puro con design tokens en lugar de Tailwind** — menos dependencias en la fase inicial; los tokens (`--up`, `--down`, etc.) centralizan la paleta de estados que usará toda la app (cards, badges, gráficos).
4. **Polling cada 30 s en el dashboard** — suficiente para el MVP; se sustituirá por WebSockets/SSE cuando exista el scheduler de checks real.
5. **Enums duplicados (Pydantic ↔ TypeScript)** — duplicación consciente y pequeña; si crece, se puede generar el cliente TS desde el OpenAPI del backend.
6. **`pip install --user` en el entorno cloud** — el entorno no tiene `python3-venv`; en local se recomienda venv normal (ver README).
