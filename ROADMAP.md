# Roadmap de upCheck

## Fase 0 — Scaffold ✅

- [x] Monorepo: `backend/` (FastAPI) + `frontend/` (React + Vite + TS)
- [x] API v1 con endpoints de monitores y Swagger
- [x] Dashboard responsive: stats, cards de monitores, refresco automático
- [x] Docker Compose (Postgres 17 + backend + frontend), Makefile, tests de humo

## Fase 1 — MVP (en progreso)

- [x] Modelos SQLAlchemy (`Monitor`, `CheckResult`) + migraciones Alembic
- [x] Scheduler de checks con Celery + Redis (HTTP, TCP)
- [x] `POST /monitors` para crear monitores
- [x] Stats de uptime 24h calculadas desde historial real
- [ ] CRUD completo desde la UI (editar/eliminar)
- [ ] Historial de resultados por monitor (endpoint + UI)
- [ ] Alertas por email al cambiar UP → DOWN

## Fase 2 — Diferenciadores

- [ ] Checks de bases de datos: PostgreSQL, MySQL, Redis, MongoDB
- [ ] Métricas de latencia (p50/p95) y uptime % (7d/30d/90d) con gráficos
- [ ] Sistema de incidentes (agrupar fallos consecutivos)
- [ ] Status page pública
- [ ] Webhooks / Slack / Telegram
- [ ] Aviso de expiración de certificados SSL
- [ ] Ventanas de mantenimiento

## Fase 3 — Nivel pro

- [ ] Auth multi-usuario (JWT) y roles
- [ ] WebSockets para dashboard en tiempo real
- [ ] Endpoint `/metrics` compatible con Prometheus
- [ ] Assertions en checks (status + contenido del body)
- [ ] Reportes periódicos por email
- [ ] CI con GitHub Actions (lint + tests + build)
