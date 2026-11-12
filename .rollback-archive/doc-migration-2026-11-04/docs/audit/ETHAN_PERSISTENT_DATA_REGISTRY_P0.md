# ETHAN — Registre des données à préserver (P0, audit seulement)

Aucune migration ni suppression n'a été lancée.

## 1. Inventaire de données persistantes

| Type | Emplacement / mécanisme | Source de vérité candidate | Remarques |
|---|---|---|---|
| Utilisateurs/rôles/API keys | PostgreSQL `user` table + migrations `003_create_users_table.sql`, `006_add_totp_2fa.sql` | `core/auth` (Core) | Conserver schéma jusqu'à plan |
| Providers LLM | PostgreSQL table providers (`004_create_llm_providers_table.sql`) + CoreWebUIStore | `core/llm` (Core) | Résoudre duplication |
| Config globale EFAN/Ethan | PostgreSQL config + CoreWebUIStore settings | Core config | Inférer depuis migrations et router v1 |
| Knowledge / RAG documents | collections managers + upload/partage | Core knowledge/rag | Besoin inventaire volumes vectoriels |
| Chat history | `core/state/chats.py` ChatStore | Core state | Vérifier présence des données réelles |
| Memory/facts/events | `CoreWebUIStore` + memory/facts core | managers réels | Risque de doublon |
| Skills | SkillStore + webui skills | `core/skills` | Stabiliser import/validation |
| Plugins/custom/plugin registry | PluginRegistry + CoreWebUIStore | Core plugins | Seed defaults |
| Missions/tasks | MissionManager | Core missions | état à vérifier |
| Files metadata + physical files | FileStore + `/var/lib/ethan` paths + archives | Core state/files | Ne pas supprimer archives |
| Logs | `logs/`, btscanner.log, testdisk.log, nohup outputs | observabilité | non métier mais preuves |
| NATS event store | NATS JetStream streams | event bus | Replay fragile |
| Archives/backups | `.rollback-archive`, `pg_backup` service, `/var/lib/ethan/archives` | ops | préserver |
| Modèles locaux | `models/`, Ollama host externe | provider Ollama | Ne pas réinstaller |
| Caches/build | `.next`, `.pytest_cache`, `.ruff_cache`, rust target | artefacts | peut être régénéré, mais conserver en P0 |
| Secrets/config locale | `.env`, `.secrets`, `.aws`, `.codex`, `.agents` | config | ne jamais committer; permissions |
| OID/Obsidian knowledge | `Odsidian/` | knowledge humain | préserver (hors scope code) |

## 2. Variables d'environnement à préserver

Sources: `.env.example`, `.env.v2.example`, `docker-compose*.yml`.

Prioritaires:
- Secrets: `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `JWT_SECRET`, `NATS_TOKEN`, `OPEN_WEBUI_SECRET_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `ETHAN_API_KEY`, MCP sandbox vars.
- Connexions: `DATABASE_URL`, `REDIS_URL`, `NATS_URL`, `OLLAMA_BASE_URL`, `VLLM_BASE_URL`, `CUSTOM_OPENAI_BASE_URL`.
- Ports: `API_PORT`, `NATS_PORT`, `REDIS_PORT`, `POSTGRES_PORT`, `ETHAN_WEBUI_PORT`, `ETHAN_WEBUI_DEV_PORT`, `OPEN_WEBUI_PORT`, `GRAFANA_PORT`, etc.
- Feature flags: `ENABLE_LEARNING`, `ENABLE_METACOGNITION`, `ENABLE_AUTONOMY`.
- Obs: Loki/Grafana/Vault/OTEL.

## 3. Migrations et schéma

- PostgreSQL migrations: `deploy/postgres/migrations/001..009` + Alembic (`deploy/postgres/alembic`).
- SQLite et state composite: `core/state/*.py`, `core/facts/store.py` schema.
- Actions interdites pendant P0: migrer, dropper, réécrire schémas.

## 4. Inconnues ops

- Volumes Docker non visibles (permission daemon).
- Applications de migrations actuelles non confimées.
- Existence de données locales dans `/var/lib/ethan` non vérifiée dans ce sandbox.
