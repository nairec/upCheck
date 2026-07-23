# upCheck

Plataforma de monitoreo de infraestructura: revisa periódicamente el estado de servidores, servicios y bases de datos, con dashboard web, historial y alertas.

**Stack:** FastAPI + PostgreSQL (backend) · React + Vite + TypeScript (frontend) · Docker Compose

## Quick start

Con Docker (recomendado):

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API + Swagger: http://localhost:8000/docs

Sin Docker:

```bash
# Terminal 1 — backend
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
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

Fase actual: **scaffold** — estructura del monorepo, API con datos de ejemplo y dashboard conectado. Ver [ROADMAP.md](ROADMAP.md) para las siguientes fases.
