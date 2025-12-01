.PHONY: install-backend install-frontend ingest backend-test backend-lint frontend-test frontend-lint test lint

install-backend:
\tpip install -e .[dev]

install-frontend:
\tcd frontend && npm install

ingest:
\tpython -m backend.app.rag.ingestion

backend-test:
\tpytest

backend-lint:
\tblack backend --check
\tisort backend --check-only
\truff backend
\tmypy backend

frontend-test:
\tcd frontend && npm test

frontend-lint:
\tcd frontend && npm run lint

test: backend-test frontend-test

lint: backend-lint frontend-lint
