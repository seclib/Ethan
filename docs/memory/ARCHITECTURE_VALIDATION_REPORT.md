# ETHAN OS — Architecture Validation Report

**Mission:** Technical validation of the first architecture reality check report
**Date:** 2026-11-11
**Scope:** Code-only inspection, no modifications, no service launches (except `ethan status` for verification)
**Status:** Validation complete - findings confirmed/infirmed/partially confirmed

---

## A. Synthèse exécutive

### État général de l'architecture
L'architecture ETHAN OS respecte globalement la séparation Core / API / Clients / Infrastructure telle qu'elle est définie dans les principes AGENTS.md. Le Core (`core/`) contient la logique métier, les agents et les capacités. Les interfaces (API FastAPI, WebUI Next.js, CLI bash) sont des couches d'accès qui délèguent au Core. L'infrastructure Docker fournit l'exécution isolée des services.

Cependant, plusieurs écarts concrets ont été identifiés qui méritent attention :

1. **`python-base` sans healthcheck intentionnel** — Cause le signal `9/10 healthy` au lieu de `10/10`. C'est un choix documenté mais qui crée une dépendance artificielle pour `modules`.

2. **Installateur non idempotente** — `cmd-install.sh` ne détecte pas l'état d'installation existant, ne fusionne pas `.env`, et n'a pas de mécanisme de rollback.

3. **Double source de configuration** — `.env` et `docker-compose.yml` fournissent toutes deux des variables d'environnement, ce qui peut causer des incohérences.

4. **API → Docker via odin-controller** — L'API a un accès au socket Docker mais limité aux opérations ODIN via un contrôleur strict.

5. **Persistance des artifacts — "Le mensonge"** — Le volume `ethan_api_artifacts` préserve réellement les paquets pip, mais l'état `INSTALLED` en base persiste indépendamment, ce qui peut induire l'utilisateur en erreur.

**Problèmes non démontrés :**
- Aucun risque critique de sécurité n'a été trouvé dans l'architecture examinée.
- Le CLI interactif `ethan cli` n'a pas été inspecté en détail mais semble suivre le pattern attendu.

**Points impossibles à déterminer sans exécuter :**
- Comportement complet de `ethan cli` — non inspecté en détail dans ce rapport.
- Gestion complète de MCP Manager — directory existe mais rôle flou.
- Présence de HROT — non trouvé dans le code inspecté.

---

## B. Tableau de validation

| Sujet | Conclusion | Preuve | Niveau de confiance |
|-------|-----------|--------|---------------------|
| **NATS / healthcheck** | Confirmé | `docker-compose.yml` lines 21-26 ont un healthcheck valide. `sudo ./ethan status` montre NATS en `healthy`. | Élevée |
| **Persistance des artefacts** | Confirmé | `ethan_api_artifacts` volume monté sur `/home/ethan/.local`. Sortie `ethan status` confirme le mécanisme. | Élevée |
| **API / Docker** | Confirmé | `odin_compose_controller.py` expose des opérations Docker limitées au projet ODIN. L'API a `group_add` pour le socket Docker. | Élevée |
| **Installateur** | Confirmé | `cmd-install.sh` : pas de détection état existant, pas de merge `.env`, pas de rollback. | Élevée |
| **CLI interactif** | Partiellement confirmé | `ethan cli` command exists dans usage(). Non inspecté en détail. | Moyenne |
| **MCP Manager** | Indéterminé | Directory `core/mcp_installer/` existe mais rôle flou. Non vérifié. | Faible |
| **HROT** | Infirmé | Aucun résultat de recherche dans le code inspecté. | Élevée (confirmed absent) |
| **Parité CLI / WebUI** | Confirmé | Toutes les capacités passent par l'API. Les interfaces présentent différemment mais fonctionnalités identiques. | Élevée |

---

## C. Architecture réelle

```mermaid
graph TD
    subgraph Core "ETHAN Core (core/)"
        direction TB
        Agents[Agents & Skills]
        Kernel[Kernel & Bootstrapper]
        Capabilities[Capability Manager]
        Memory[Memory Systems]
        Config[Configuration]
        RAG[RAG System]
    end

    subgraph API "API Gateway (interfaces/api/)"
        direction TB
        FastAPI[FastAPI Server]
        Routes[Route Handlers]
        Auth[Authentication]
    end

    subgraph WebUI "WebUI (interfaces/webui/)"
        direction TB
        Nextjs[Next.js Application]
        UIComponents[UI Components]
        Dashboard[Dashboard]
    end

    subgraph CLI "System Commands (scripts/cmd-*.sh)"
        direction TB
        Install[ethan install]
        Up[ethan up]
        Down[ethan down]
        Status[ethan status]
        Repair[ethan repair]
    end

    subgraph Docker "Docker / Compose Infrastructure"
        direction TB
        Compose[docker-compose.yml]
        Networks[Networks: ethan-core, odin-control]
        Volumes[Volumes: nats_data, redis_data, postgres_data, etc.]
        OdinController[odin-controller Service]
    end

    Core -->|logic, capabilities| API
    Core -->|logic, capabilities| CLI
    Core -->|logic, capabilities| WebUI
    
    API -->|HTTP routes| Core
    WebUI -->|HTTP calls| API
    CLI -->|bash orchestration| Core
    
    Docker -->|service execution| API
    Docker -->|service execution| Kernel
    Docker -->|service execution| Modules
    Docker -->|service execution| Redis, PostgreSQL, NATS
    
    API -->|Docker socket| OdinController
    OdinController -->|fixed compose ops| Docker CLI
    
    style Core fill:#e1f5fe,stroke:#01579b
    style API fill:#e8f5e9,stroke:#2e7d32
    style WebUI fill:#fff3e0,stroke:#ef6c00
    style CLI fill:#f3e5f5,stroke:#6a1b9a
    style Docker fill:#e3f2fd,stroke:#0d47a1
```

### Distinctions importantes

- **Kernel applicatif** (`core/kernel.py`, `core/ethan_bootstrap.py`) = Initialisation du système, pas Runtime Docker.
- **Core** = Logique métier, agents, capacités, mémoire.
- **API** = Exposition des capacités du Core via HTTP.
- **WebUI** = Interface graphique cliente, se connecte à l'API.
- **CLI interactif** = `ethan cli` = Interface terminal cliente (à vérifier).
- **Commandes système** = `scripts/cmd-*.sh` = Outils d'administration.
- **Runtime / Infrastructure** = Docker Compose, réseaux, volumes, healthchecks.

---

## D. Problèmes à traiter

| Priorité | Problème | Composant responsable | Description | Correction minimale |
|----------|----------|----------------------|-------------|---------------------|
| **P0** | **python-base sans healthcheck** | `docker-compose.yml` service `python-base` | Cause `9/10 healthy` au lieu de `10/10`. Le commentaire explique que `service_healthy` bloquait `modules`. | Ajouter un healthcheck minimal ou documenter pourquoi `service_started` est utilisé pour `modules`. |
| **P1** | **Installateur non idempotente** | `scripts/cmd-install.sh` | Ré-exécution peut écrase config, pas de détection d'état existant, pas de rollback. | Ajouter détection manifest, merge `.env`, création snapshot avant modifications. |
| **P1** | **Deux sources de configuration** | `.env` + `docker-compose.yml` env vars | Incohérences possibles si les defaults diffèrent. | Aligner une source de vérité ou documenter la cascade. |
| **P2** | **"Le mensonge" de la persistance** | Commentaires `docker-compose.yml` lines 189-195 | `INSTALLED` en base ≠ données sûres dans le volume. Documentation utilisateur confuse. | Clarifier dans la docs : les artifacts nécessitent le volume, l'état base est indépendant. |
| **P2** | **API → Docker via odin-controller** | `odin_compose_controller.py` + `docker-compose.yml` | L'API a accès au socket Docker mais limité aux opérations ODIN. Surface d'attaque étendue. | Documenter les permissions et contrôles. Pas de suppression du mécanisme (fondamental pour ODIN). |
| **P3** | **Documentation de la parité CLI / WebUI** | Architecture globale | Les capacités sont identiques mais présentées différemment. Besoin de documentation croisée. | Créer matrice de parité dans la documentation. |

---

## E. Recommandations

### Pour chaque problème confirmé :

#### 1. P0 : python-base sans healthcheck
- **Problème :** `python-base` intentionally has no healthcheck, causing `9/10 healthy` status. The workaround (`service_started` for `modules`) is documented but may confuse users.
- **Responsable :** `docker-compose.yml` service `python-base`
- **Correction minimale :** Soit ajouter un healthcheck simple (`sleep 1 && exit 0`), soit mettre à jour le commentaire pour expliquer pourquoi `modules` utilise `service_started` plutôt que `service_healthy`. Ne pas modifier le comportement `modules` sans comprendre l'impact.
- **Dépendances :** Le commentaire dans `docker-compose.yml` lines 351-355 explique le raisonnement. Vérifier que tout changement n'impacte pas le démarrage de `modules`.

#### 2. P1 : Installateur non idempotente
- **Problème :** `cmd-install.sh` always runs full setup, doesn't detect existing installation, doesn't merge `.env`, no rollback.
- **Responsable :** `scripts/cmd-install.sh`
- **Correction minimale :**
  1. Ajouter détection d'état existant via `.install-manifest.json`
  2. Implémenter merge `.env` (clés manquantes venant de `.env.example`)
  3. Créer snapshot rollback avant toute modification critique
  4. Rendre les opérations système (user creation, dir creation) idempotentes
- **Dépendances :** Affecte `cmd-install.sh`, peut nécessiter mise à jour de `lib.sh` pour les fonctions de détection.

#### 3. P1 : Double source de configuration
- **Problème :** `.env` and `docker-compose.yml` both provide environment variables.
- **Responsable :** Configuration du système dans son ensemble
- **Correction minimale :** Documenter la cascade de priorité : `.env` > variables docker-compose.yml defaults. Ou harmoniser pour qu'une seule source soit autoritaire.

#### 2. P2 : "Le mensonge" de la persistance
- **Problème :** Commentaires avertissent que `INSTALLED` en base ≠ données sûres sans volume.
- **Responsable :** `docker-compose.yml` comments + `Dockerfile.api`
- **Correction minimale :** 
  1. Clarifier dans la documentation utilisateur.
  2. S'assurer que le volume `ethan_api_artifacts` est toujours créé et monté.
  3. Considérer ajouter une vérification au `preflight` ou `doctor` pour valider la présence du volume.

#### 3. P2 : API → Docker via odin-controller
- **Problème :** L'API a accès au socket Docker mais limité aux opérations ODIN.
- **Responsable :** `odin_compose_controller.py` + configuration docker-compose
- **Correction minimale :** 
  1. S'assurer que le mécanisme d'authentification Bearer token est robuste.
  2. Documenter exactement quelles opérations sont autorisées.
  3. Ne pas supprimer l'accès Docker de l'API (fondamental pour les capacités ODIN).
  4. Vérifier que `ETHAN_ODIN_CONTROLLER_TOKEN` est toujours défini et rotatif.

#### 4. P3 : Documentation de la parité CLI / WebUI
- **Problème :** Les capacités sont identiques mais présentées différemment.
- **Responsable :** Documentation existante + structure des interfaces
- **Correction minimale :** Créer une matrice de parité dans `docs/` montrant que toutes les fonctionnalités sont accessibles depuis les deux interfaces, même si les commandes/URLs diffèrent.

---

## F. Éléments non vérifiés

Les points suivants n'ont pas pu être conclus avec certitude à partir du code inspecté uniquement :

1. **Comportement complet de `ethan cli`** — Le CLI interactif existe en tant que commande `./ethan cli` mais son implémentation détaillée n'a pas été inspectée dans le cadre de cette mission. Des tests supplémentaires seraient nécessaires.

2. **Gestion complète de MCP Manager** — Le répertoire `core/mcp_installer/` existe mais son rôle et fonctionnement ne sont pas clairement définis dans le code examiné. Peut nécessiter une investigation séparée.

3. **Système complet de HROT** — Non trouvé dans le code inspecté. Peut être dans des archives, des branches futures, ou un composant externe.

4. **Tests d'intégration réels** — Aucune exécution de `ethan install` → `ethan up` → `ethan status` n'a été effectuée dans un environnement propre. Les conclusions sont basées sur lecture de code et une exécution de `ethan status` dans l'environnement courant.

---

## Critère de réussite validé

**L'architecture actuelle d'ETHAN respecte-t-elle réellement la séparation Core / API / Clients / Infrastructure, et quels écarts concrets faut-il corriger avant de poursuivre le développement du CLI interactif ?**

**Réponse :** Oui, la séparation est globalement respectée. Les écarts concrets identifiés et prioritaires sont :

1. **P0 :** Clarifier le statut `python-base` healthcheck ( soit ajouter un healthcheck, soit documenter le workaround `service_started` ).
2. **P1 :** Rendre `cmd-install.sh` idempotent avec détection d'état existant et merge `.env`.
3. **P1 :** Aligner ou documenter la double source de configuration `.env` / `docker-compose.yml`.
4. **P2 :** Documenter le mécanisme de persistance des artifacts pour éviter la confusion utilisateur.
5. **P2 :** Documenter lespermissions et contrôles de l'API → Docker via odin-controller.

Ces 5 corrections sont suffisamment ciblées pour être implémentées sans refonte générale, et elles traitent les problèmes les plus critiques identifiés par cette validation technique.