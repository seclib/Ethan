.PHONY: help install dev build up down logs test

help:
	@echo "Ethan Cognitive OS — Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install    Install Python dependencies"
	@echo "  make dev        Run API Gateway locally (uvicorn)"
	@echo "  make build      Build Docker images"
	@echo "  make up         Start all services (docker-compose)"
	@echo "  make down       Stop all services"
	@echo "  make logs       Follow service logs"
	@echo "  make test       Run tests"

install:
	pip install -r kernel/requirements.txt

dev:
	PYTHONPATH=. NATS_URL=nats://localhost:4222 uvicorn api.main:app --reload --port 8000

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	PYTHONPATH=. python -m pytest tests/ -v

shell:
	docker-compose exec kernel python

.PHONY: help install dev build up down logs test shell