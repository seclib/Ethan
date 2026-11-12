# ETHAN — Technical Baseline

## 1. État général

- Branche courante : `refactor/ethan-rebuild-p0`
- Worktree très dirty : nombreux fichiers modifiés et non suivis.
- Backend principal : Core + Runtime + services + interfaces.
- Interface principale : WebUI accessible sur 3001.
- Backend API historique : FastAPI, WebUI sur 3001, Kernel sur 8080.
- PostgreSQL/Redis/NATS disponibles via compose.
- Entity modules: Core en Python.

## 2. Architecture réelle

- `core/`: logique métier, LLM, mémoire, agents, auth.
- `runtime/`: orchestration et contextes.
- `services/`: infra et capacité.
- `interfaces/api/`: routes FastAPI et middleware.
- `interfaces/webui/`: Next.js WebUI, proxied.
- Les couches `/workspace/codemaps` existent partiellement.
- principal type d'ingénierie documenté par AGENTS.md.

## 3. Composants principaux

- Identité : `core/auth/principal.py`, `interfaces/api/auth.py`.
- TRUST-SERVICE : service identity foundation, HROT, admin provisioning.
- Agent manager et plugins existent mais sont touchés par refonte.
- WebUI login restauré en démarrant API sur réseau partagé.

## 4. Flux et dépendances

Les flux principaux:
- WebUI proxy → FastAPI → RBAC/Trusted principal
- HUMAN → JWT
- INTERNAL SERVICE (HROT approvals!)
- Core manager/Audit.
- PostgreSQL as authoritative where configured.

## 5. Points forts

- source durable de confiance pour TRUST-SERVICE 2.4.
- tests targeted ~50 successful
- HROT persisté en PostgreSQL when DATABASE_URL set.

## 6. Limites

- Deux voies de persistance HROT (pg + JSONL)
- Terminal WS still failing
- Many untracked changes
- Athrus / agent harness non thoroughly validated.
- Documentation sometimes ahead of code.

## 7. Principes de dépendance

- Corps via Core plutôt qu'inteface
- Identity derived from middleware only
- No destructive git actions in this environment.

