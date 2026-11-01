.PHONY: venv install backend frontend run test lint

venv:
	python3 -m venv .venv
	source .venv/bin/activate
	pip install --upgrade pip
	pip install -e "backend[dev]" -e "frontend[dev]"

install:
	pip install -e "backend[dev]" -e "frontend[dev]"

# backend:
# 	cd backend && uvicorn app.main:app --reload --port 8000

# frontend:
# 	cd frontend && python -m app.main

backend:
	PYTHONPATH=backend uvicorn app.main:app --reload --port 8000

frontend:
	PYTHONPATH=frontend python -m app.main

run:
	set -e; \
	PYTHONPATH=backend uvicorn app.main:app --port 8000 & \
	pid=$$!; \
	trap 'kill $$pid' EXIT INT TERM; \
	PYTHONPATH=frontend python -m app.main

test:
	cd backend && python -m pytest -q
	cd frontend && python -m pytest -q

lint:
	ruff check backend frontend
