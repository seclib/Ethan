.PHONY: help install dev build up down logs test lint clean shell bootstrap doctor preflight pull-images wait-for-services status smoke ci

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
	@echo "  make bootstrap  Séquence de boot complète (preflight → pull → up → wait → status)"
	@echo "  make doctor     Diagnostiquer l'installation"
	@echo "  make preflight  Vérifier les prérequis système"
	@echo "  make pull-images Pré-télécharger les images Docker"
	@echo "  make status    Afficher l'état des services"
	@echo "  make smoke     Vérifier la stack de bout en bout (health, auth, chat, projects)"

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
	./ethan preflight
	./ethan pull-images
	./ethan up --skip-preflight --skip-pull
	./ethan wait-for-services
	./ethan status

doctor:
	./ethan doctor

preflight:
	./ethan preflight

pull-images:
	./ethan pull-images

wait-for-services:
	./ethan wait-for-services

status:
	./ethan status

smoke:
	./ethan smoke

ci: lint test
	docker compose build --parallel