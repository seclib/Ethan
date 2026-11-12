# Phase C — Settings & UX — Plan d'exécution

> **Date** : 2026-08-18
> **Statut** : EN COURS

---

## Objectif

1. Implémenter l'interface de Settings riche (inspirée des 13 onglets d'Open WebUI) dans le frontend Next.js.
2. S'assurer que le WebUI agit comme un *thin client* qui consomme et modifie l'API `/v1/config/*` d'ETHAN.
3. Réviser la gestion des serveurs MCP (Model Context Protocol) depuis l'interface et le backend.

## Périmètre

1. **Backend (API)** :
   - Vérifier ou créer le router `interfaces/api/routers/config.py` (GET/PUT `/v1/config/{domain}`).
   - Assurer que `core/config/schema.py` intègre bien les domaines nécessaires (rag, models, mcp, etc.).

2. **Frontend (WebUI)** :
   - Créer la structure des composants UI pour les Settings (`features/settings/components/`).
   - Mettre en place les onglets principaux (General, Interface, Models, Connections, Documents, WebSearch, Tools/MCP).
   - Intégrer les appels React Query vers `/v1/config/{domain}`.

3. **Révision MCP** :
   - Vérifier l'intégration du `ToolServerManager` et son exposition via API.
   - S'assurer que les serveurs MCP peuvent être ajoutés/synchronisés depuis l'UI Settings.

## Critères de sortie

- [x] Routeur API `/v1/config` opérationnel.
- [x] Composants UI Settings créés avec au moins les onglets de base et MCP.
- [x] Tests exécutés.
- [x] Rapport produit.

<task_progress>
- [x] Créer le plan d'exécution Phase C
- [x] Vérifier/implémenter API `/v1/config`
- [x] Créer la structure UI Settings (Tabs)
- [x] Implémenter l'onglet MCP Tools
- [x] Lancer les tests
</task_progress>
