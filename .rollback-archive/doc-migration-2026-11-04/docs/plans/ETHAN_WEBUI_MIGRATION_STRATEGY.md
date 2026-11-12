# Stratégie de migration — Ancienne WebUI ETHAN → ETHAN WebUI (fork Open WebUI)

> **Architecture validée** :
> ```
> Open WebUI → fork → ETHAN WebUI → ETHAN API → ETHAN Core / Runtime
> ```
> **Principe** : migration **réversible**, progressive, par étapes. **Aucune suppression irréversible sans validation.** L'ancienne WebUI reste fonctionnelle jusqu'à la bascule finale.
> **Aucun fichier source `.py` / `.tsx` modifié.** Nouveau document `docs/plans/`.

---

## 0. Principes de la migration

### 0.1 Réversibilité
- Chaque étape est **indépendante** et **réversible** (rollback = revert du commit Git).
- L'ancienne WebUI reste **déployable** jusqu'à l'étape 20.
- Aucune donnée n'est migrée de façon destructive (copie, jamais suppression).

### 0.2 Rituel par étape (obligatoire)
À **chaque** étape, avant de passer à la suivante :

| Vérification | Commande / Méthode | Critère de succès |
|---|---|---|
| **Tests** | `pytest` (backend) + `npm test` (frontend) | 0 échec |
| **Build** | `npm run build` (frontend) + `uv build` (backend) | build OK |
| **Vérification API** | `curl` sur les endpoints concernés | 200/201 attendus |
| **Vérification Docker** | `docker compose build` + `docker compose up` | conteneurs healthy |
| **Vérification UI** | navigation manuelle / smoke test | fonctionnalité visible |
| **Commit Git** | `git add` + `git commit -m "étape N: ..."` | commit atomique |

### 0.3 Branches Git
```
main            → stable (ancienne WebUI fonctionnelle)
feature/webui-migration → branche de migration (toutes les étapes)
  ├── step-01-fork
  ├── step-02-ethan-webui
  ├── ...
  └── step-20-deprecate
```
- Chaque étape = **1 commit** sur `feature/webui-migration`.
- Rollback = `git revert <commit>`.

### 0.4 Coexistence des deux WebUI
```
interfaces/webui/          → ANCIENNE WebUI (Next.js) — reste fonctionnelle
interfaces/webui-ethan/    → NOUVELLE WebUI (fork Open WebUI) — en construction
```
- Les deux coexistent pendant toute la migration.
- Le routeur (Traefik/nginx) bascule le trafic progressivement (canary).

---

## 1. Préparer le fork Open WebUI

**Objectif** : créer un fork propre et versionné d'Open WebUI.

| Action | Détail |
|---|---|
| Fork | `git clone https://github.com/open-webui/open-webui` → `interfaces/webui-ethan/` |
| Version | Épingler une version stable (tag) |
| README | Documenter l'origine, la version, la licence |
| CI | Configurer build/test sur le fork |

**Vérifications** : build frontend OK, backend OK, Docker OK, commit `step-01-fork`.

---

## 2. Créer ETHAN WebUI

**Objectif** : renommer le projet, structure de dossiers ETHAN.

| Action | Détail |
|---|---|
| Renommage | `open-webui` → `ethan-webui` (package.json, imports) |
| Structure | Aligner sur `interfaces/webui-ethan/` |
| Config | `ethan.config.ts` (nom, version, branding) |
| Docker | `deploy/Dockerfile.ui-ethan` |

**Vérifications** : build OK, Docker OK, UI s'affiche, commit `step-02-ethan-webui`.

---

## 3. Faire fonctionner le frontend seul

**Objectif** : le frontend tourne sans backend ETHAN (mode démo/mock).

| Action | Détail |
|---|---|
| Mock API | Intercepteur de requêtes (MSW ou mock local) |
| Routes | Toutes les pages s'affichent (chat, settings, admin) |
| Données | Données de démo (modèles, conversations factices) |

**Vérifications** : UI complète navigable, build OK, commit `step-03-frontend-seul`.

---

## 4. Ajouter le branding ETHAN

**Objectif** : identité visuelle ETHAN.

| Action | Détail |
|---|---|
| Logo | Remplacer le logo Open WebUI par ETHAN |
| Couleurs | Thème ETHAN (CSS variables) |
| Nom | `ETHAN` partout (titre, favicon, meta) |
| Footer | Version ETHAN + licence |

**Vérifications** : branding visible, build OK, commit `step-04-branding`.

---

## 5. Connecter l'authentification ETHAN

**Objectif** : le frontend s'authentifie via ETHAN API.

| Action | Détail |
|---|---|
| Endpoint | `POST /v1/auth/login` (ETHAN API) |
| Token | JWT ETHAN stocké (cookie/localStorage) |
| Logout | `POST /v1/auth/logout` |
| Session | Vérification `GET /v1/auth/me` |

**Vérifications** : login/logout OK, token valide, API vérifiée, commit `step-05-auth`.

---

## 6. Connecter Models

**Objectif** : afficher les modèles depuis ETHAN Core.

| Action | Détail |
|---|---|
| Endpoint | `GET /v1/models` (ETHAN API → `core/llm/model_store`) |
| Liste | Afficher les modèles disponibles |
| Sélection | Choisir un modèle actif |

**Vérifications** : liste modèles OK, sélection OK, commit `step-06-models`.

---

## 7. Connecter Providers

**Objectif** : gérer les providers depuis ETHAN Core.

| Action | Détail |
|---|---|
| Endpoint | `GET/PUT /v1/providers` (ETHAN API → `core/llm/provider_manager`) |
| Liste | Afficher les providers (Ollama, OpenAI, …) |
| Config | Modifier base_url, modèle par défaut (sans secrets) |
| Test | `POST /v1/providers/{id}/test` (healthcheck) |

**Vérifications** : providers listés, config OK, test OK, commit `step-07-providers`.

---

## 8. Connecter Conversations

**Objectif** : lister/ouvrir les conversations depuis ETHAN Core.

| Action | Détail |
|---|---|
| Endpoint | `GET /v1/chats` (ETHAN API → `core/state/chats`) |
| Liste | Afficher les conversations |
| Ouverture | Charger une conversation |
| Nouvelle | Créer une conversation |

**Vérifications** : liste OK, ouverture OK, création OK, commit `step-08-conversations`.

---

## 9. Connecter Files

**Objectif** : upload/listing des fichiers via ETHAN Core.

| Action | Détail |
|---|---|
| Endpoint | `POST/GET /v1/files` (ETHAN API → `core/state/files`) |
| Upload | Envoyer un fichier |
| Liste | Afficher les fichiers |
| Preview | Afficher le contenu |

**Vérifications** : upload OK, liste OK, preview OK, commit `step-09-files`.

---

## 10. Connecter Knowledge

**Objectif** : collections de connaissance via ETHAN Core.

| Action | Détail |
|---|---|
| Endpoint | `GET/POST /v1/knowledge` (ETHAN API → `core/knowledge`) |
| Liste | Afficher les collections |
| Création | Créer une collection |
| Fichiers | Associer des fichiers à une collection |

**Vérifications** : collections OK, fichiers associés OK, commit `step-10-knowledge`.

---

## 11. Connecter RAG

**Objectif** : retrieval RAG via ETHAN Core.

| Action | Détail |
|---|---|
| Endpoint | `POST /v1/retrieval/query` (ETHAN API → `core/rag`) |
| Ingestion | `POST /v1/retrieval/process/file` |
| Config | `GET/PUT /v1/config/rag` |
| Chat RAG | Intégrer le retrieval dans le chat |

**Vérifications** : ingestion OK, query OK, chat RAG OK, commit `step-11-rag`.

---

## 12. Connecter MCP

**Objectif** : serveurs MCP via ETHAN Core.

| Action | Détail |
|---|---|
| Endpoint | `GET/POST /v1/tools/servers` (ETHAN API → `core/tools/servers`) |
| Liste | Afficher les serveurs MCP |
| Création | Ajouter un serveur (URL, auth) |
| Test | `POST /v1/tools/servers/{id}/test` |

**Vérifications** : serveurs listés, création OK, test OK, commit `step-12-mcp`.

---

## 13. Connecter Tools

**Objectif** : outils appelables via ETHAN Core.

| Action | Détail |
|---|---|
| Endpoint | `GET/POST /v1/tools` (ETHAN API → `core/tools/registry`) |
| Liste | Afficher les outils (builtin + custom) |
| Activation | Toggle actif/inactif |
| Exécution | Appeler un outil dans le chat |

**Vérifications** : outils listés, activation OK, exécution OK, commit `step-13-tools`.

---

## 14. Connecter Memory

**Objectif** : mémoire ETHAN via Core.

| Action | Détail |
|---|---|
| Endpoint | `GET/POST /v1/memory` (ETHAN API → `core/facts` / `core/memory`) |
| Liste | Afficher les faits/mémoires |
| Ajout | Ajouter un fait |
| Suppression | Supprimer un fait |

**Vérifications** : faits listés, ajout OK, suppression OK, commit `step-14-memory`.

---

## 15. Connecter Agents / Atreus

**Objectif** : agents et Atreus via ETHAN Core.

| Action | Détail |
|---|---|
| Endpoint | `GET/POST /v1/agents` (ETHAN API → `core/agents`) |
| Liste | Afficher les agents |
| Configuration | Configurer un agent (modèle, mémoire) |
| Atreus | Lancer un agent autonome |

**Vérifications** : agents listés, config OK, Atreus OK, commit `step-15-agents`.

---

## 16. Connecter Settings

**Objectif** : configuration via ETHAN Core (voir `ETHAN_WEBUI_SETTINGS_ARCHITECTURE.md`).

| Action | Détail |
|---|---|
| Endpoint | `GET/PUT /v1/config/{domain}` (ETHAN API → `core/config`) |
| Schema | `GET /v1/config/schema` (JSON Schema → Form) |
| Pages | 13 onglets admin + user settings |
| Secrets | Jamais exposés (secrets.py) |

**Vérifications** : settings affichés, mise à jour OK, secrets masqués, commit `step-16-settings`.

---

## 17. Connecter les permissions

**Objectif** : RBAC ETHAN appliqué au frontend.

| Action | Détail |
|---|---|
| Endpoint | `GET /v1/auth/me` (rôles/permissions) |
| Guards | Masquer/afficher les actions selon permissions |
| Admin | Routes admin protégées |
| User | Routes user protégées |

**Vérifications** : admin voit tout, user limité, commit `step-17-permissions`.

---

## 18. Tester chaque domaine

**Objectif** : validation complète de tous les domaines connectés.

| Domaine | Test |
|---|---|
| Auth | login/logout, session, permissions |
| Models | liste, sélection |
| Providers | liste, config, test |
| Conversations | liste, ouverture, création |
| Files | upload, liste, preview |
| Knowledge | collections, fichiers |
| RAG | ingestion, query, chat |
| MCP | serveurs, test |
| Tools | liste, activation, exécution |
| Memory | faits, ajout, suppression |
| Agents | liste, config, Atreus |
| Settings | affichage, mise à jour |
| Permissions | RBAC |

**Vérifications** : tous les tests passent, build OK, Docker OK, commit `step-18-tests`.

---

## 19. Basculer progressivement

**Objectif** : canary deployment — bascule progressive du trafic.

| Phase | Trafic | Durée |
|---|---|---|
| Canary 1% | 1% du trafic → ETHAN WebUI | 1 semaine |
| Canary 10% | 10% | 1 semaine |
| Canary 50% | 50% | 1 semaine |
| Full | 100% | — |

**Vérifications** : monitoring (erreurs, latence), rollback possible à tout moment, commit `step-19-bascule`.

---

## 20. Déprécier l'ancienne WebUI

**Objectif** : après validation complète, déprécier l'ancienne WebUI.

| Action | Détail |
|---|---|
| Freeze | Ancienne WebUI en lecture seule (pas de nouvelles features) |
| Archive | Déplacer vers `interfaces/webui-legacy/` |
| Documentation | Noter la dépréciation |
| Suppression | **Seulement après 2 semaines de stabilité** — suppression définitive |

> ⚠️ **Aucune suppression irréversible sans validation.** La suppression n'intervient qu'après :
> - 2 semaines de 100% trafic sur ETHAN WebUI
> - 0 incident bloquant
> - Backup complet de l'ancienne WebUI

**Vérifications** : ancienne WebUI archivée, ETHAN WebUI stable, commit `step-20-deprecate`.

---

## Récapitulatif des étapes

| # | Étape | Commit | Réversible |
|---|---|---|---|
| 1 | Préparer le fork | `step-01-fork` | ✅ |
| 2 | Créer ETHAN WebUI | `step-02-ethan-webui` | ✅ |
| 3 | Frontend seul | `step-03-frontend-seul` | ✅ |
| 4 | Branding | `step-04-branding` | ✅ |
| 5 | Auth | `step-05-auth` | ✅ |
| 6 | Models | `step-06-models` | ✅ |
| 7 | Providers | `step-07-providers` | ✅ |
| 8 | Conversations | `step-08-conversations` | ✅ |
| 9 | Files | `step-09-files` | ✅ |
| 10 | Knowledge | `step-10-knowledge` | ✅ |
| 11 | RAG | `step-11-rag` | ✅ |
| 12 | MCP | `step-12-mcp` | ✅ |
| 13 | Tools | `step-13-tools` | ✅ |
| 14 | Memory | `step-14-memory` | ✅ |
| 15 | Agents / Atreus | `step-15-agents` | ✅ |
| 16 | Settings | `step-16-settings` | ✅ |
| 17 | Permissions | `step-17-permissions` | ✅ |
| 18 | Tests | `step-18-tests` | ✅ |
| 19 | Bascule progressive | `step-19-bascule` | ✅ |
| 20 | Dépréciation | `step-20-deprecate` | ⚠️ après validation |

---

## Conclusion

La migration est **progressive, réversible, testée à chaque étape**. L'ancienne WebUI reste fonctionnelle jusqu'à la bascule finale. Aucune suppression irréversible sans validation complète (2 semaines de stabilité, 0 incident, backup).
</write_to_file>
<task_progress>
- [x] Analyser le feedback (stratégie de migration réversible en 20 étapes)
- [x] Définir les principes de migration (réversibilité, rituel par étape, branches Git, coexistence)
- [x] Rédiger les 20 étapes avec actions détaillées
- [x] Rédiger le récapitulatif des étapes (commits, réversibilité)
- [x] Créer le document docs/plans/ETHAN_WEBUI_MIGRATION_STRATEGY.md
</task_progress>
</write_to_file>