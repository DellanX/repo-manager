.PHONY: dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend install install-backend install-frontend clean

# Development
dev: dev-backend dev-frontend

dev-backend:
	cd backend && .venv/bin/python -m uvicorn src.server:app --host 0.0.0.0 --port 8888 --reload

dev-frontend:
	cd frontend && npm run dev

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && .venv/bin/pytest

test-frontend:
	cd frontend && npm run test:unit

# Linting
lint: lint-backend lint-frontend

lint-backend:
	cd backend && .venv/bin/ruff check src tests

lint-frontend:
	cd frontend && npm run lint

# Installation
install: install-backend install-frontend

install-backend:
	cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -e .

install-frontend:
	cd frontend && npm install

# Cleanup
clean:
	rm -rf backend/.venv backend/.pytest_cache backend/.ruff_cache backend/.coverage
	rm -rf frontend/node_modules frontend/dist
