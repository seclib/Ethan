# Mission 09 — Phase D — Matrice des opérations d'écriture contrôlées

**Nature** : préparation uniquement. Aucune opération d'écriture réelle n'a été exécutée.  
**Date** : 2026-11-11. Branche : `refactor/ethan-rebuild-p0`.

## 1. Inventaire des commandes d'écriture CLI

### Providers
| CLI | API | Permission | Core service |
|---|---|---|---|
| `provider create` | `POST /providers` | PLUGINS | `ProviderManager.create()` |
| `provider update` | `PUT /providers/{id}` | PLUGINS | `ProviderManager.update()` |
| `provider delete` | `DELETE /providers/{id}` | PLUGINS | `ProviderManager.delete()` |
| `provider test` | `POST /providers/{id}/test` | PLUGINS | `ProviderManager.test()` |
| `provider default` | `PUT /providers/{id}/default` | PLUGINS | `ProviderManager.set_default()` |

### Models
| CLI | API | Permission | Core service |
|---|---|---|---|
| `model pull` | `POST /models/pull` | PLUGINS | `ModelManager.pull()` |

### Agents
| CLI | API | Permission | Core service |
|---|---|---|---|
| `agent create` | `POST /v1/agents` | WRITE | `AgentManager.create()` |
| `agent update` | `PUT /v1/agents/{id}` | WRITE | `AgentManager.update()` |
| `agent delete` | `DELETE /v1/agents/{id}` | WRITE | `AgentManager.delete()` |
| `agent run/execute` | `POST /v1/agents/{id}/execute` | EXECUTE | `AgentManager.execute()` |

### Applications
| CLI | API | Permission | Core service |
|---|---|---|---|
| `application refresh` | `POST /v1/applications/refresh` | PLUGINS | `_refresh_catalogs()` |
| `application start` | `POST /v1/applications/{id}/start` | PLUGINS | `get_odin_service().start()` |
| `application stop` | `POST /v1/applications/{id}/stop` | PLUGINS | `get_odin_service().stop()` |
| `application validate` | `POST /v1/application-capabilities/validate` | READ | `ApplicationCapabilityContract.validate()` |
| `application register` | `POST /v1/application-capabilities` | PLUGINS | `register_application_capability()` |
| `application bind` | `POST /v1/application-capabilities/{id}/bind` | PLUGINS | `bind_capability_implementation()` |
| `application activate` | `POST /v1/application-capabilities/{id}/activate` | PLUGINS | `activate_capability_binding()` |
| `application invoke` | `POST /v1/application-capabilities/{id}/invoke` | EXECUTE | `invoke_application_capability()` |

### Knowledge
| CLI | API | Permission | Core service |
|---|---|---|---|
| `knowledge create` | `POST /v1/knowledge` | WRITE | `KnowledgeManager.create()` |
| `knowledge update` | `PUT /v1/knowledge/{id}` | WRITE | `KnowledgeManager.update()` |
| `knowledge delete` | `DELETE /v1/knowledge/{id}` | WRITE | `KnowledgeManager.delete()` |
| `knowledge collection create` | `POST /v1/knowledge/collections` | WRITE | `KnowledgeManager.create_collection()` |
| `knowledge collection-update` | `PUT /v1/knowledge/collections/{id}` | WRITE | `KnowledgeManager.update_collection()` |
| `knowledge collection-move` | `POST /v1/knowledge/collections/{id}/move` | WRITE | `KnowledgeManager.move_collection()` |
| `knowledge collection-delete` | `DELETE /v1/knowledge/collections/{id}` | WRITE | `KnowledgeManager.delete_collection()` |
| `knowledge document-add` | `POST /v1/knowledge/collections/{id}/documents` | WRITE | `KnowledgeManager.add_document()` |
| `knowledge document-delete` | `DELETE .../documents/{doc_id}` | WRITE | `KnowledgeManager.delete_document()` |
| `knowledge reindex` | `POST /v1/knowledge/collections/{id}/reindex` | WRITE | `KnowledgeManager.reindex()` |
| `knowledge connect` | `POST /v1/knowledge/{id}/connections` | WRITE | `KnowledgeManager.connect()` |

### Memory
| CLI | API | Permission | Core service |
|---|---|---|---|
| `memory record` | `POST /v1/memory/events` | RECORD | `EngineeringMemoryService.record()` |
| `memory validate` | `POST /v1/memory/events/validate` | RECORD | `EngineeringMemoryService.validate()` |
| `memory vault-write` | `POST /v1/memory/vault/file` | RECORD | `VaultService.write()` |

### Sessions
| CLI | API | Permission | Core service |
|---|---|---|---|
| `session create` | `POST /chats` | WRITE | `ChatStore.create_chat()` |
| `session update` | `PUT /chats/{id}` | WRITE | `ChatStore.update_chat()` |
| `session delete` | `DELETE /chats/{id}` | WRITE | `ChatStore.delete_chat()` |
| `session add` | `POST /chats/{id}/messages` | WRITE | `ChatStore.add_message()` |
| `session share` | `POST /chats/{id}/share` | WRITE | `ChatStore.share_chat()` |

### MCP
| CLI | API | Permission | Core service |
|---|---|---|---|
| `mcp add` | `POST /v1/tools/servers` | PLUGINS | `ToolServerManager.create()` |
| `mcp update` | `PUT /v1/tools/servers/{id}` | PLUGINS | `ToolServerManager.update()` |
| `mcp enable/disable` | `PUT /v1/tools/servers/{id}` (enabled) | PLUGINS | `ToolServerManager.update()` |
| `mcp remove` | `DELETE /v1/tools/servers/{id}` | PLUGINS | `ToolServerManager.delete()` |
| `mcp sync` | `POST /v1/tools/servers/{id}/sync` | PLUGINS | `ToolServerManager.sync_tools()` |

### Skills
| CLI | API | Permission | Core service |
|---|---|---|---|
| `skill create` | `POST /v1/skills` | WRITE | `SkillManager.create()` |
| `skill update` | `PUT /v1/skills/{id}` | WRITE | `SkillManager.update()` |
| `skill delete` | `DELETE /v1/skills/{id}` | WRITE | `SkillManager.delete()` |
| `skill toggle` | `POST /v1/skills/{id}/toggle` | WRITE | `SkillManager.toggle()` |
| `skill run` | `POST /v1/skills/{id}/run` | EXECUTE | `SkillManager.run()` |

### Missions
| CLI | API | Permission | Core service |
|---|---|---|---|
| `mission create` | `POST /v1/missions` | WRITE | `MissionManager.create()` |
| `mission update` | `PUT /v1/missions/{id}` | WRITE | `MissionManager.update()` |
| `mission delete` | `DELETE /v1/missions/{id}` | WRITE | `MissionManager.delete()` |

### Chat / Exec
| CLI | API | Permission | Core service |
|---|---|---|---|
| `chat` (one-shot) | `POST /v1/chat/completions` | WRITE | `ChatPipeline` |
| `exec` | `POST /v1/system/exec/operations` | EXECUTE | `ExecutionManager` |
| `exec cancel` | `POST /v1/system/exec/operations/{id}/cancel` | EXECUTE | `ExecutionManager.cancel()` |

### Approval
| CLI | API | Permission | Core service |
|---|---|---|---|
| `approval resolve` | `POST /internal/approval/resolve` | ADMIN | `ApprovalEngine.resolve()` |

## 2. HROT permission matrix

| Permission | Routes utilisant |
|---|---|
| READ | GET (list, show, get) |
| WRITE | POST/PUT/DELETE (create, update, delete, chat, knowledge, sessions, skills, missions) |
| PLUGINS | POST/PUT/DELETE (providers, applications, MCP, refresh) |
| EXECUTE | POST (agent run, capability invoke, exec) |
| RECORD | POST (memory events, vault write) |
| ADMIN | POST (approval resolve) |

Toutes les permissions sont vérifiées côté API via `require_permission(Permission.*)`. Le CLI ne contourne pas HROT.

## 3. Stratégie de test isolé

Pour chaque domaine, le test matrix couvre :

1. **Create** → vérifier la réponse (ID, champs).
2. **Read after create** → vérifier la cohérence.
3. **Update** → vérifier les champs modifiés.
4. **Read after update** → vérifier la cohérence.
5. **Delete** → vérifier la suppression (404 après).
6. **Validation failure** → payload invalide → 422.
7. **Unauthorized** → sans token → 401.
8. **Not found** → ID inexistant → 404.

### Ressources de test proposées (isolées)

- Providers : utiliser un provider `test-provider` (type `custom`, URL `http://localhost:9999`).
- Agents : agent nommé `test-agent-m09` avec capabilities vides.
- Knowledge : entrée `test-knowledge-m09` avec contenu minimal.
- Sessions : session titre `test-session-m09`.
- MCP : serveur `test-mcp-m09` désactivé (`enabled=false`).
- Skills : skill `test-skill-m09` avec contenu minimal.
- Missions : mission `test-mission-m09`.
- Memory : événement avec `component=test`, `record_type=engineering_event`.
- Vault : fichier `test-m09.md` avec contenu minimal.

### Risques

- Les tests d'écriture réels modifient l'état Core (base de données, fichiers vault).
- Les ressources de test doivent être nettoyées (delete) après validation.
- Les tests doivent utiliser des noms uniques pour éviter les collisions.
- Les permissions HROT doivent être vérifiées avec un token sans les droits requis (pas de contournement).

### Dépendances

- API Core doit être démarrée et authentifiée.
- Token avec permissions suffisantes (admin ou PLUGINS+WRITE+EXECUTE+RECORD).
- Aucune dépendance externe (Ollama, qdrant) pour les tests d'écriture basiques.

## 4. Fichiers qui nécessiteraient modification (si exécution autorisée)

Aucun fichier n'a besoin de modification pour la préparation. Les commandes CLI existantes couvrent toutes les opérations d'écriture listées.

## 5. Statut

**Préparation terminée. En attente d'autorisation explicite pour exécuter les opérations d'écriture réelles.**

Aucune modification de code ou de données n'a été effectuée.
