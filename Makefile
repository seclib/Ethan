.PHONY: help install dev build up down logs test lint clean shell bootstrap doctor preflight pull-images wait-for-services status smoke ci dev-code dev-ui

help:
	@echo "Ethan Cognitive OS — Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install    Install Python package in editable mode"
	@echo "  make dev        Run API Gateway locally (uvicorn)"
	@echo "  make dev-code   Dev : bind mounts du code (overlay dev) + restart api/kernel/modules — zéro rebuild"
	@echo "  make dev-ui     Dev : WebUI en mode hot-reload (next dev, port 3002) — zéro rebuild"
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
	PYTHONPATH=. NATS_URL=nats://localhost:$(NATS_PORT) uvicorn api.main:app --reload --port $(API_PORT)

# Dev sans rebuild : active les bind mounts de code (docker-compose.dev.yml)
# puis recrée les services applicatifs — le code source du host est lu
# directement, un changement Python se voit après simple restart.
dev-code:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --no-build api kernel modules

# WebUI en hot-reload (next dev + bind mount, port 3002) : aucun rebuild
# nécessaire pour développer l'interface. Voir docker-compose.dev.yml (ui-dev).
dev-ui:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d ui-dev

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

# ── Ports dev locaux (surchargeurs : env ou `make dev API_PORT=9000`) ──
API_PORT ?= 8000
NATS_PORT ?= 4222
