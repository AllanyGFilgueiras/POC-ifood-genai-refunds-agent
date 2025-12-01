.PHONY: install-backend install-frontend ingest backend-test backend-lint frontend-test frontend-lint test lint

install-backend:
	pip install -e .[dev]

install-frontend:
	cd frontend && npm install

ingest:
	python -m backend.app.rag.ingestion

backend-test:
	pytest

backend-lint:
	black backend
	isort backend
	ruff backend
	mypy backend

frontend-test:
	cd frontend && npm run test -- --runInBand

frontend-lint:
	cd frontend && npm run lint

test: backend-test frontend-test

lint: backend-lint frontend-lint
