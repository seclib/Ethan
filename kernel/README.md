# ETHAN Kernel — Go Runtime

Noyau du système ETHAN. Orchestre les modules Python via NATS et expose une API HTTP.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   HTTP      │────▶│   Gateway    │────▶│   Router    │
│   Clients   │     │   (Gin)      │     │   (NATS)    │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                            ┌────▼─────┐
                                            │  NATS    │
                                            │  JetStream│
                                            └────┬─────┘
                                                 │
                         ┌───────────────────────┼───────────────────────┐
                         │                       │                       │
                    ┌────▼─────┐           ┌────▼─────┐           ┌────▼─────┐
                    │ Module   │           │ Module   │           │ Module   │
                    │ Executive│           │ Planner  │           │ Memory   │
                    │ (Python) │           │ (Python) │           │ (Python) │
                    └──────────┘           └──────────┘           └──────────┘
```

## Composants

| Composant | Fichier | Responsabilité |
|-----------|---------|----------------|
| **main.go** | Entrypoint | Démarrage, flags, config, shutdown |
| **gateway** | gateway/gateway.go | HTTP server (Gin), routes API |
| **router** | router/router.go | Connexion NATS, publication events |
| **modules** | modules/manager.go | Spawn/supervise workers Python |

## Démarrage rapide

### Prérequis

- Go 1.21+
- NATS server (local ou distant)
- Python 3.10+ avec les modules ETHAN installés

### Build

```bash
cd kernel
go mod tidy
go build -o ethan-kernel
```

### Configuration

Copier `ethan.yaml.example` vers `ethan.yaml` et adapter :

```yaml
agents:
  executive:
    enabled: true
    auto_start: true
    module: core.agents.executive
  planner:
    enabled: true
    auto_start: true
    module: core.agents.planner
  memory:
    enabled: true
    auto_start: true
    module: core.agents.memory
```

### Exécution

```bash
# Démarrage basique
./ethan-kernel --nats-url nats://localhost:4222

# Avec config personnalisée
./ethan-kernel --config ./ethan.yaml --nats-url nats://prod:4222
```

### Endpoints HTTP

| Méthode | Path | Description |
|---------|------|-------------|
| GET | /health | Health check |
| POST | /api/v1/chat | Envoyer un message |
| GET | /api/v1/status | Statut du système |
| POST | /api/v1/command | Exécuter une commande |

### Exemples

```bash
# Health check
curl http://localhost:8080/health

# Chat
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "bonjour", "session_id": "abc123"}'

# Status
curl http://localhost:8080/api/v1/status
```

## Modules Python

Chaque module est un processus Python indépendant qui :

1. Se connecte à NATS
2. S'abonne aux events qui l'intéressent
3. Publie des events en réponse
4. Envoie un heartbeat périodique

### Exemple de module minimal

```python
# core/agents/example.py
import asyncio
from core.agents.base import Agent, AgentConfig

class ExampleAgent(Agent):
    async def _on_event(self, event):
        print(f"Received: {event.type}")

    async def run(self, input_data=None):
        return {"status": "ok"}

if __name__ == "__main__":
    import sys
    import logging
    logging.basicConfig(level=logging.INFO)
    
    config = AgentConfig(name="example")
    agent = ExampleAgent(config=config)
    asyncio.run(agent.start())
```

## Monitoring

Le kernel expose :

- **Logs structurés** : JSON lines sur stdout
- **Métriques** : à venir (Prometheus)
- **Tracing** : correlation_id sur chaque event

## Arrêt propre

```bash
# SIGINT (Ctrl+C) ou SIGTERM
kill -TERM <pid>
```

Le kernel :
1. Arrête les modules (SIGTERM, puis SIGKILL après 5s)
2. Ferme les connexions NATS
3. Libère les ressources

## Développement

### Structure du projet

```
kernel/
├── go.mod
├── main.go
├── gateway/
│   └── gateway.go
├── router/
│   └── router.go
└── modules/
    └── manager.go
```

### Ajouter une route

```go
// gateway/gateway.go
func (s *Server) setupRoutes() {
    s.engine.GET("/health", s.healthCheck)
    s.engine.POST("/api/v1/chat", s.handleChat)
    s.engine.GET("/api/v1/status", s.handleStatus)
    // Nouvelle route
    s.engine.GET("/api/v1/modules", s.handleModules)
}
```

## Limitations MVP

- Pas d'authentification (à venir)
- Pas de TLS (à venir)
- Pas de rate limiting (à venir)
- Request/reply synchrone non implémenté (retourne "accepted")

## Prochaines étapes

- [ ] Implémenter request/reply avec timeout
- [ ] Ajouter l'authentification (API key, JWT)
- [ ] Métriques Prometheus
- [ ] Healthcheck des modules (heartbeat NATS)
- [ ] Configuration dynamique (reload sans restart)