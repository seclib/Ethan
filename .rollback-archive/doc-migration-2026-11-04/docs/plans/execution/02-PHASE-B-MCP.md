# Phase B — MCP — Plan d'exécution

> **Date** : 2026-08-18
> **Statut** : EN COURS

---

## Objectif

Intégrer un client MCP (Model Context Protocol) natif dans `core/tools/mcp_client.py` en s'inspirant de l'implémentation de référence Open WebUI, et le brancher sur le `ToolRegistry` et `ToolServerManager` d'ETHAN.

## Périmètre

1. **Client MCP** : Reporter `open_webui/utils/mcp/client.py` dans `core/tools/mcp_client.py` (streamable_http + stdio).
2. **Registry** : Modifier `core/tools/registry.py` et `core/tools/servers.py` pour enregistrer les outils découverts via le client MCP.
3. **Tests** : Ajouter des tests unitaires pour `mcp_client.py`.

## Critères de sortie

- [x] `core/tools/mcp_client.py` implémenté.
- [x] `ToolServerManager` mis à jour pour initier le client.
- [x] `ToolRegistry` mis à jour pour introspecter les tools.
- [x] Tests exécutés.
- [x] Rapport produit.

<task_progress>
- [x] Analyser open_webui/utils/mcp/client.py
- [x] Implémenter core/tools/mcp_client.py
- [x] Adapter core/tools/servers.py
- [x] Adapter core/tools/registry.py
- [x] Lancer les tests et valider
</task_progress>
