# upCheck

Plataforma de monitoreo de infraestructura: revisa periódicamente el estado de servidores, servicios y bases de datos, con dashboard web, historial y alertas.

**Stack:** FastAPI + PostgreSQL + Celery + Redis (backend) · React + Vite + TypeScript (frontend) · Docker Compose

## Quick start

Con Docker (recomendado):

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API + Swagger: http://localhost:8000/docs

Servicios adicionales: **Redis** (broker Celery), **celery-worker** (ejecuta checks), **celery-beat** (dispara checks cada 30 s).

Sin Docker (requiere Postgres y Redis locales):

```bash
# Terminal 1 — migraciones + API
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Celery worker
make worker

# Terminal 3 — Celery beat
make beat

# Terminal 4 — frontend
cd frontend && npm install && npm run dev
```

El frontend hace proxy de `/api` hacia `http://localhost:8000` en desarrollo (ver `frontend/vite.config.ts`).

## Estructura del monorepo

```
upcheck/
├── backend/          # API FastAPI (Python 3.12)
│   ├── app/
│   │   ├── api/      # Routers y endpoints
│   │   ├── core/     # Database, infraestructura
│   │   ├── models/   # Modelos SQLAlchemy
│   │   └── schemas/  # Schemas Pydantic
│   └── tests/
├── frontend/         # SPA React + Vite + TypeScript
│   └── src/
│       ├── api/        # Cliente HTTP
│       └── components/ # Componentes UI
├── docker-compose.yml
└── Makefile
```

Más detalle en [estructura.md](estructura.md).

## Comandos útiles

```bash
make test     # Tests del backend (pytest)
make lint     # Ruff + oxlint
make build    # Build de producción del frontend
make up       # Docker Compose up
```

## Estado del proyecto

Fase actual: **MVP en progreso** — modelos SQL, Celery scheduler, checks HTTP/TCP y API conectada a PostgreSQL. Ver [ROADMAP.md](ROADMAP.md).
