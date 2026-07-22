.PHONY: help install dev build up down logs test lint clean

help:
	@echo "Ethan Cognitive OS — Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install    Install Python package in editable mode"
	@echo "  make dev        Run API Gateway locally (uvicorn)"
	@echo "  make build      Build Docker images"
	@echo "  make up         Start all services (docker-compose)"
	@echo "  make down       Stop all services"
	@echo "  make logs       Follow service logs"
	@echo "  make test       Run tests"
	@echo "  make lint       Run linter (ruff)"
	@echo "  make clean      Remove __pycache__ and .pyc files"
	@echo "  make bootstrap  Full boot sequence (doctor + up + wait + status)"

install:
	pip install -e ".[server,dev]"

dev:
	PYTHONPATH=. NATS_URL=nats://localhost:4222 uvicorn api.main:app --reload --port 8000

build:
	docker compose build

up:
	./ethan up

down:
	./ethan down

logs:
	docker compose logs -f

test:
	pytest tests/ -v

lint:
	ruff check core/ interfaces/ plugins/ sdk/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

shell:
	docker compose exec kernel python

bootstrap:
	./ethan doctor
	./ethan up
	scripts/cmd-wait-for-services.sh
	./ethan status

ci: lint test
	docker compose build --parallel