# ETHAN — Architecture du Engineering Memory Service

Date : 2026-11-03
Statut : PROPOSED

## 1. Objet

Ce document décrit une architecture réalisable, non obligatoirement implémentée, pour un Memory Service attaché à ETHAN.

Il ne crée aucun comportement runtime et ne modifie pas le code.

## 2. Composants et responsabilités

### 2.1 Memory Service

Responsabilités :

- accepter les événements et les enregistrements ;
- appliquer les politiques d'autorisation ;
- coordonner la validation, la persistence et l'indexation ;
- gérer les versions et provenance ;
- offrir les API de consultation.

Boundary : Python dans `core/` et `interfaces/api`.

### 2.2 Event Collector

Responsabilités :

- recevoir des événements depuis les composants et les agents ;
- distinguer `observed` et `declared` ;
- normaliser les champs ;
- dispatcher au Validation Engine.

Points d'intégration réels :

- `core/events/` et `core.ethan_types.event` ;
- `core/bus.memory_bus.InMemoryBus` ;
- `core/bus/backends/rust_event_store` en mode shadow ;
- `core/knowledge/agent_traces` et `core/knowledge/agent_traces/sync_engine.py`.

### 2.3 Validation Engine

Responsabilités :

- valider contre `EventSchemaRegistry` ;
- vérifier les transitions de statut ;
- contrôler la provenance ;
- rejeter les états incohérents.

Réutilise :

- `core/registry/events.py`
- `core/capability_manager`
- `core/cognition/reflector` si nécessaire pour les helpers de raisonnement.

### 2.4 Persistence Adapter

Responsabilités :

- écrire dans Obsidian de façon atomique ;
- append dans les journaux ;
- mettre à jour les index ;
- synchroniser avec la persistance relationnelle existante.

Réutilise :

- `core/persistence/manager.py` et backends ;
- `core/persistence/migrations.py` ;
- `core/persistence/storage.py`.

### 2.5 Registry

Responsabilités :

- résoudre les mappings de type, destination et schéma ;
- gérer les IDs et les relations ;
- vérifier l'existence et les politiques ;
- exposer les métadonnées.

Réutilise les ressources Obsidian existantes et les schémas de routage.

### 2.6 Query / Retrieval API

Responsabilités :

- retrouver par composant, statut, date, auteur, relation ;
- renvoyer motifs et preuves ;
- préparer la requête pour les agents et l'humain.

Réutilise les routeurs FastAPI et `core/search`.

### 2.7 Indexation

Responsabilités :

- maintenir l'index relationnel entre événements, composants, preuves et incidents ;
- mettre à jour les synthèses ;
- garder les graphes optionnels, jamais obligatoires.

### 2.8 Audit Trail

Responsabilités :

- tracer chaque écriture ;
- conserver l'origine ;
- permettre l'export probant et la restauration ;
- intégrer Git et Obsidian tampon.

## 3. Contrat d'interface minimal

```json
{
  "id": "EVT-2026-001",
  "type": "event",
  "status": "RECORDED",
  "source_type": "observed | declared",
  "source_of_fact": "path_or_command",
  "components": ["CMP-YYYY-NNN"],
  "people": ["human", "agent"],
  "summary": "",
  "evidence_refs": [],
  "timestamp": "ISO8601",
  "confidence": "medium"
}
```

## 4. Mapping Rust / Python

### Python

- Memory Service
- Validation et schemas
- RBAC et auth
- Persistance documentaire
- Knowledge ingestion
- RAG et providers
- tests

### Rust

- Event store backend `core/bus/backends/rust_event_store`
- métrique santé `core/rust/ethan_health`
- accélération optionnelle pour hachage/indexation bas-niveau
- journalisation append-only si charge élevée

### Règle

Les chemins chauds et accélérés passent par des adaptateurs. Le moteur de jugement reste Python.

## 5. Contraintes et architecture de livraison

- Obsidian reste un dossier normal, lisible sans GUI.
- pas de base graphique obligatoire.
- pas de store central concurrent.
- chaque enregistrement doit inclure provenance et statut.
- la publication externe demande une sélection + une redaction + un scan.

## 6. Points d'intégration au dépôt

Les intégrations possibles sont :

- `core/registry/events.py` pour la validation ;
- `core/persistence` pour l'accès disque ;
- `core/bus/memory_bus` pour le transport ;
- `interfaces/api/routers` pour l'exposition ;
- `core/knowledge/agent_traces` pour l'ingestion et la synchronisation ;
- `core/auth` et `core/security` pour l'autorisation ;
- `core/capability_manager` pour l'état des composants ;
- `Obsidian` pour la source documentaire.

## 7. Matrice des composants et responsabilités

| Composant | Responsabilité | Technologie | Persistance | Dépendance |
|---|---|---|---|---|
| Memory Service | orchestration et règles | Python | Obsidian + DB | Auth/RBAC |
| Event Collector | capture d'événements | Python + option Rust | journal + stream | bus |
| Validation Engine | schémas et transitions | Python | registre schémas | registry |
| Persistence Adapter | writes + atomique | Python | Obsidian + backends | pty |
| Registry | destination, ID, relations | Python | fichiers + DB | schema store |
| Query API | filtrage et consultation | FastAPI | API | auth |
| Indexation | relation et résumé | Python | DB/index | memory service |
| Audit Trail | hashes et tracking | Python | Obsidian + Git | event log |

## 8. Risques et dépendances bloquantes

1. Obsidian n'est pas dans Git.
2. Les schémas sont actuellement des gabarits et non encore une base de test.
3. Les audt et events ne partagent pas un modèle computationnel commun.
4. La navigation dans l'index Source B doit être arbitratée.
5. Les références aux chemins historiques nécessitent des tests.
6. L'orchestration d'agents et les capabilities existent, mais sans enregistrement institutionnel central.
7. Le système `EventSchemaRegistry` existe déjà et peut être étendu.
8. Aucune preuve actuelle ne montre que tous les tests critiques sont réexécutés.

## 9. Plan de migration

### Phase 0 — Conception et validation
- valider ce document ;
- valider les schémas ;
- valider les transitions ;
- arbitrer les ADR officiels dans `docs/adr` si nécessaire.

### Phase 1 — Indexation et lecture
- exposer des routes de consultation ;
- produire un index relationnel ;
- faire la traçabilité des événements sans écrire de conclusion.

### Phase 2 — Écriture
- validation stricte des schémas ;
- write atomique ;
- rollback et hashes ;
- journal d'audit.

### Phase 3 — Intégration progressive
- plugins et outils écrivent des events ;
- agents déposent des AgentReports ;
- Obsidian tampon ;
- tests et dashboards peuvent lire.

### Phase 4 — Gouvernance
- incubation ;
- révisions et nouveaux cas ;
- correction sans rétroaction silencieuse ;
- archive de versions.

## 10. Vérifications réellement disponibles

- Pas d'implémentation effectuée.
- Les documents sont cohérents entre eux.
- La source de vérité reste `core/`.
- Les services existants sont réutilisables.
- Aucune dépendance nouvelle introduite.

## 11. Conclusion

Cette architecture est crédible avec le dépôt actuel et elle n'impose pas une réécriture générale. Le Memory Service doit partir des événements existants, des schémas, de la persistance et de l'authentification, puis imposer la provenance et le statut.

L'Engineering Memory reste observationnelle et prophylactique : un système de gardien de cohérence, pas une nouvelle base concurrente.
