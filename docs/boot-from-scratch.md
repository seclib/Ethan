# Boot depuis un système vierge

## Prérequis machine
- Docker
- Docker Compose
- Python 3.10+
- Node.js (pour `ethan webui`)
- Git

## Étapes minimales
```bash
git clone <repo> && cd Ethan
cp .env.example .env
./ethan install
./ethan up
./ethan doctor
./ethan status
```

## Vérification
- `/health` API
- `http://localhost:3000`
- `docker compose ps`

## En cas d’échec
- `./ethan doctor --verbose`
- `docker compose logs <service>`