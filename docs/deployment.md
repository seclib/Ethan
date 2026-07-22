# Déploiement ETHAN

## Prérequis

- Docker + Docker Compose
- Python 3.11+ + venv
- Node.js 20+ (pour WebUI)
- Git

## Installation rapide

```bash
./ethan install
```

## Démarrer l'environnement complet

```bash
./ethan up
```

Services exposés :
- WebUI : http://localhost:3000
- API : http://localhost:8000/health
- NATS : http://localhost:8222

## Commandes essentielles

```bash
./ethan status          # État des services
./ethan logs api -f     # Logs en temps réel
./ethan restart api     # Redémarrer un service
./ethan down            # Arrêter tout
./ethan doctor          # Diagnostic
```

## Production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Systemd

```bash
sudo cp infrastructure/systemd/ethan-core.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ethan-core
```

## Notes

- `docker-compose.prod.yml` : overrides production (NODE_ENV, LOG_LEVEL, replicas API)
- `docker-compose.dev.yml` : extensions dev (optionnelles)
- Les scripts `install/` sont dépréciés, utiliser `./ethan`