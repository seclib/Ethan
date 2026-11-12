# Phase A — Consolidation — Plan d'exécution

> **Date** : 2026-08-17
> **Statut** : EN COURS
> **Décision** : Périmètre Phase A validé par l'utilisateur (2026-08-17)

---

## Objectif

Vérifier que le repository ETHAN est dans un état sain avant toute modification de code (Phase B et suivantes).

## Périmètre

1. **Tests backend** : `pytest` sur `core/`, `interfaces/api/`, `tests/`.
2. **Tests frontend** : `npm run validate` (= `typecheck` + `lint` + `test`).
3. **Build frontend** : `npm run build`.
4. **Build Docker** : `docker compose build` (ou au minimum les images clés).

## Rituel (par étape)

| Vérification | Commande | Critère de succès |
|---|---|---|
| Tests backend | `pytest` | 0 échec |
| Typecheck frontend | `npm run typecheck` | EXIT 0 |
| Lint frontend | `npm run lint` | EXIT 0 |
| Tests frontend | `npm test` | PASS |
| Build frontend | `npm run build` | build OK |
| Build Docker | `docker compose build` | images construites |

## Résultats

| Étape | Résultat | Statut |
|---|---|---|
| A1 — pytest (test_ethan_core) | 37 passed | ✅ |
| A1b — pytest (tests/ complet) | 1292 collectés, 424 erreurs (411 openjarvis, 6 cli, 2 core.plugins) | ⚠️ BLOQUÉ |
| A2 — typecheck frontend | `tsc --noEmit` EXIT 0 | ✅ |
| A3 — lint frontend | 1 erreur corrigée (`chat-sidebar.tsx` : `<a>`→`<Link>`) → EXIT 0 | ✅ |
| A4 — tests frontend | 5 suites, 7 tests PASS | ✅ |
| A5 — build frontend | 25 routes compilées (Next.js) | ✅ |
| A6 — build Docker | 5 images : ethan-ui, ethan-api, ethan-kernel, ethan-modules, ethan-pg_backup | ✅ |

## Critères de sortie

- [x] Tous les tests frontend passent (7/7)
- [x] Le build frontend passe (25 routes)
- [x] Le build Docker passe (5 images)
- [x] Les résultats sont documentés dans ce fichier
- [ ] Tous les tests backend passent (bloqué par B1/B2/B3 — dépendances externes)

## Récapitulatif des corrections effectuées

### C1 — `core/config/secrets.py` : implémentation de `SecretManager`
- **Constat** : `tests/test_ethan_core/conftest.py` et `test_secret_manager.py` importaient `SecretManager` et `SecretNotFoundError` depuis `core.config.secrets`, mais ce module ne contenait que `Secrets` et `get_secrets()`.
- **Correction** : ajout de `SecretManager` (cache, conventions `ETHAN_<NAME>`, `get`, `get_or_none`, `clear_cache`) et `SecretNotFoundError`.
- **Justification** : `Obsidian/Engineering/Audits/00-ETAT-DES-LIEUX.md` §2.1 — `core/config/` doit exposer une gestion de secrets unifiée. Les tests sont la spécification de l'API attendue.
- **Validation** : 9 tests SecretManager + 37 tests test_ethan_core PASS.

### C2 — `chat-sidebar.tsx` : correction lint `<a>` → `<Link>`
- **Constat** : 1 erreur ESLint (`@next/next/no-html-link-for-pages`) sur le lien `/`.
- **Correction** : remplacement des 3 `<a href>` par `<Link href>` + import `next/link`.
- **Justification** : conformité aux bonnes pratiques Next.js (documentées dans `ETHAN_WEBUI_V2_ARCHITECTURE.md` §1 — Next.js 15 App Router).
- **Validation** : lint EXIT 0, typecheck EXIT 0, build 25 routes OK.

## Bloqueurs identifiés

### B1 — Dépendance externe manquante : `openjarvis` (411 erreurs)
- **Cause** : `tests/operators/test_operators.py` importe `openjarvis.*` (package externe hébergé sur `openjarvis.ai`).
- **Constat** : le module n'est pas installé dans le venv (`.venv/lib/python3.11/site-packages/` ne contient pas `openjarvis`).
- **Impact** : 411 tests de collecte échouent (ModuleNotFoundError).
- **Décision** : ne pas installer de dépendance externe sans validation (règle : pas de modification d'infrastructure sans RFC). **Bloqueur documenté, à valider avec l'utilisateur.**

### B2 — Module `cli` manquant (6 erreurs)
- **Cause** : certains tests `tests/cli/` importent `cli` qui n'est pas résolu.
- **Impact** : 6 erreurs de collecte.

### B3 — Module `core.plugins` manquant (2 erreurs)
- **Cause** : 2 tests importent `core.plugins` qui n'existe pas dans `core/`.
- **Impact** : 2 erreurs de collecte.

> **Note** : les 37 tests de `tests/test_ethan_core/` passent (dont les 9 nouveaux tests SecretManager). Le blocage concerne uniquement les tests dépendant de modules externes/absents.

## Prochaine étape (après validation)

- Phase B — MCP : ajouter le client MCP complet → `core/tools/mcp_client.py`.
</write_to_file>
<task_progress>
- [x] Créer le rapport d'état des lieux (00-ETAT-DES-LIEUX.md)
- [x] Créer le plan d'exécution Phase A (01-PHASE-A-CONSOLIDATION.md)
- [x] A1 — pytest backend
- [x] A2 — typecheck frontend
- [x] A3 — lint frontend
- [x] A4 — tests frontend
- [x] A5 — build frontend
- [x] A6 — build Docker
- [x] Documenter les résultats
</task_progress>
</write_to_file>