.PHONY: dev backend frontend worker beat test lint build up down install

backend:
	cd backend && python3 -m alembic upgrade head && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

worker:
	cd backend && celery -A app.worker.celery_app worker --loglevel=info

beat:
	cd backend && celery -A app.worker.celery_app beat --loglevel=info

install:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install
	cd backend && alembic upgrade head

test:
	cd backend && python3 -m pytest tests/ -v

lint:
	cd backend && python3 -m ruff check app tests
	cd frontend && npm run lint

build:
	cd frontend && npm run build

up:
	docker compose up --build

down:
	docker compose down
