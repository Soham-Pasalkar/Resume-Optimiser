.PHONY: help setup dev-backend dev-frontend test test-backend test-frontend docker-up docker-down migrate lint

help:
	@echo "CareerPilot — Developer Commands"
	@echo "--------------------------------------------------------"
	@echo "make setup          Create Python venv and install dependencies"
	@echo "make dev-backend    Start FastAPI backend development server"
	@echo "make dev-frontend   Start Next.js frontend development server"
	@echo "make test           Run all tests (backend + frontend)"
	@echo "make test-backend   Run pytest test suite"
	@echo "make test-frontend  Run frontend unit tests"
	@echo "make migrate        Apply database migrations with Alembic"
	@echo "make docker-up      Start all services with Docker Compose"
	@echo "make docker-down    Stop Docker Compose services"
	@echo "make lint           Run code formatting and lint checks"

setup:
	@echo "Setting up Python virtual environment..."
	python3.11 -m venv venv || python3.12 -m venv venv || python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r backend/requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Setup complete! Copy .env.example to .env to configure."

dev-backend:
	cd backend && ../venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	cd backend && ../venv/bin/pytest tests/ -v

test-frontend:
	cd frontend && npm test

migrate:
	cd backend && ../venv/bin/alembic upgrade head

docker-up:
	docker compose up -d

docker-down:
	docker compose down

lint:
	cd backend && ../venv/bin/ruff check .
	cd frontend && npm run lint
