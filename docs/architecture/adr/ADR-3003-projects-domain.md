# ADR-3003 — Domaine `Projects`

**Statut** : Proposition (brouillon)
**Date** : 2026-09-07
**Contexte** : Le score d'expérience workspace (AnythingLLM / Odysseus / Open WebUI) exige un
concept de « Projet » regroupant conversations, connaissances et agents. Aucun domaine
`Project` n'existe dans le Core — le WebUI ne peut pas l'inventer (AGENTS.md).

**Décision** :

1. Créer un contexte Core **`core/projects/`** (manager + store, réutilisant `CoreRecordStore`).
2. Un Projet est une **combinaison** :
   - *conversation container* : groupe de chats (`project_id` sur les chats) ;
   - *knowledge scope* : collections RAG + domains + folders admissibles ;
   - *execution context* : agents + missions du projet ;
   - pas de *UI construct* : le WebUI n'en est que la projection.
3. API : `POST/GET/PUT/DELETE /v1/projects` (+ association chats/collections/agents).
4. Aucune duplication : relations par ID, pas de copie.

**Conséquences** :

- Nouvelle API (versionnée — cf. ADR-3006).
- Le WebUI recevra le CRUD Projet après le Core (Phase E de la migration).
- Rétro-compatibilité : les chats sans projet continuent de fonctionner (projet virtuel « Sans projet »).

**Alternatives écartées** :

- Projet = simple étiquette côté frontend (contredit AGENTS.md — logique dans l'interface).
- Projet = réécriture de conversations (refactor massif inutile).
