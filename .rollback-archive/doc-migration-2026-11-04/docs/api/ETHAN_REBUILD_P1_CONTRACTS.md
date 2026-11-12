# ETHAN — Spécification de contrats API P1 (proposition, sans code)

## 1. Conv Netions

- UUID pour entités.
- Auth Bearer JWT via API gateway.
- Erreur JSON standard:
  ```json
  { "code": "ETHAN_VALIDATION_ERROR", "message": "...", "details": {}, "request_id": "uuid", "retryable": false }
  ```
- Content-Type JSON UTF-8.
- Idempotency-Key pour mutations longues/dupliquées.
- Pagination cursor-based.

## 2. Routes canoniques (proposées)

| Domaine | Route | Manager | Notes |
|---|---|---|---|
| Auth | /auth/* | Core auth | sessions JWT + API keys |
| Providers | /providers | ProviderManager | supprimer doublon /v1/providers |
| Models | /models | ProviderManager + model store | custom cards, ACL |
| Knowledge | /v1/knowledge | KnowledgeManager | collections |
| Documents/RAG | /v1/rag/* | RAGPipeline | upload processing states |
| Memory | /v1/memory/* | MemoryManager | user CRUD/search/reset |
| Skills | /v1/skills/* | SkillManager | validate/import/execute |
| Tools/MCP | /v1/tools/* | ToolManager | vals, select |
| Agents | /v1/agents/* | AgentManager | execution health |
| Missions | /v1/missions/* | MissionManager | task mapping |
| Files | /files | FileStore | multipart upload |
| Jobs | /v1/jobs/* | orchestration | progression events |
| Health | /health/* | diagnostics | SLO |

## 3. Événements longs

- SSE/WebSocket gateway.
- Statuts: queued, running, succeeded, failed, cancelled.
- Event schema: id, type, timestamp, payload, context.
- Cancel/retry borné.

## 4. Compatibilité

- Garder `/v1/chat` et message endpoints pour clients existants.
- Introduire `/v2` uniquement par ADR.
- Dépréciations documentées avec date.
