.PHONY: dev backend frontend test lint build up down

# Run both apps locally (requires two terminals, or use `make up` with Docker)
backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

install:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

test:
	cd backend && python3 -m pytest tests/ -v

lint:
	cd backend && ruff check app tests
	cd frontend && npm run lint

build:
	cd frontend && npm run build

up:
	docker compose up --build

down:
	docker compose down
