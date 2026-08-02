# Architecture Cible Authentification ETHAN OS

Ce document définit l'architecture cible pour résoudre la dette technique d'authentification identifiée (doublon entre JWT Web et RBAC mémoire) avec une priorité absolue donnée à la **stabilité**.

## 1. Séparation des Responsabilités (Target Architecture)

L'écosystème ETHAN sera divisé en deux domaines de sécurité strictement isolés :

### A. Le Domaine Public / Web (Front-facing)
**Outils :** `interfaces/api/auth.py`, FastAPI, Next.js, JWT, HTTPOnly Cookies.
**Responsabilité :** Authentifier les utilisateurs humains accédant via le portail WebUI ou les API REST publiques.
- L'utilisateur s'authentifie via le frontend.
- `interfaces/api/auth.py` gère la validation des identifiants (potentiellement via base de données plus tard), la création et la vérification des JWT.
- La session est maintenue par un Cookie HTTPOnly transféré par l'API Gateway.

### B. Le Domaine Interne / Kernel (Back-facing)
**Outils :** `core/auth/__init__.py`, NATS, API Keys internes.
**Responsabilité :** Autorisation (RBAC), quotas et communication *System-to-System* (Services, Modules, Agents, CLI).
- Le Core/Kernel ne gère **jamais** de cookies ni de mots de passe humains.
- Il se base sur des clés d'API longues (API Keys) pour identifier les services ou les agents autonomes, et applique les permissions (ex: `Permission.EXECUTE`).

**Flux unifié cible :**
```text
[Utilisateur Web] 
       ↓ (Credentials)
[API Gateway : interfaces/api/auth.py] -> Génère JWT, vérifie DB
       ↓ (JWT HTTPOnly)
[WebUI (Next.js)] -> Consomme les endpoints API
       ↓
[API Gateway] -> Vérifie JWT. Si autorisé, transforme la requête en appel interne.
       ↓ (Injecte un "Internal System Token" ou valide les droits)
[Kernel RBAC : core/auth] -> Exécute la logique métier si les droits sont suffisants.
```

---

## 2. Fichiers Concernés (Scope)

**Périmètre Web/JWT :**
- `interfaces/api/auth.py` (Validation JWT et gestion des Cookies)
- `interfaces/api/main.py` (Endpoints `/auth/login`, `/auth/me`)
- `interfaces/webui/src/core/providers/auth-provider.tsx` (Déjà corrigé, état stable)

**Périmètre Core/RBAC :**
- `core/auth/__init__.py` (La logique RBAC et la gestion des rôles à nettoyer)
- `core/memory/user_model.py` (À lier potentiellement avec la base de données utilisateur future)

---

## 3. Plan de Migration & Refactoring

> [!CAUTION]
> Ce plan garantit l'absence de régression. **Aucune fonctionnalité ne doit être migrée d'un coup**.

### Phase P0 (Critique & Immédiate) - État Stable
- **Objectif :** Nettoyer le code mort qui pourrait causer des erreurs de production.
- **Actions :**
  - Conserver le "bridge" actuel dans `main.py` qui lit le premier rôle de `core.auth.system`.
  - Supprimer le fichier fantôme `interfaces/webui/src/proxy.ts` pour éviter qu'un développeur modifie la mauvaise configuration Next.js.
  - Nettoyer le paramètre `operatorId` non-utilisé des fonctions `login()` dans le frontend.

### Phase P1 (Moyen terme) - Source de vérité (Base de données)
- **Objectif :** Remplacer le système en mémoire par PostgreSQL.
- **Actions :**
  - Créer une table `ethan.users` dans PostgreSQL via SQLAlchemy.
  - Remplacer le dictionnaire `self._users = {}` de `core/auth/__init__.py` par des appels DB.
  - Modifier `POST /auth/login` (`interfaces/api/main.py`) pour valider un hash de mot de passe en DB au lieu d'accepter n'importe quel identifiant.

### Phase P2 (Long terme) - Découplage complet
- **Objectif :** Atteindre l'architecture cible.
- **Actions :**
  - Restreindre l'import de `core/auth/__init__.py` aux stricts modules internes (Kernel, Workers).
  - L'API Gateway devient le seul validateur JWT.
  - Mettre en place un système de "Service Account" où l'API Gateway s'authentifie auprès du Kernel NATS via une API Key interne stricte, au nom de l'utilisateur.

---

## 4. Risques de Migration

1. **Régression de Session (Downtime)** : Séparer ou réécrire l'authentification backend pendant que des requêtes web sont en cours cassera toutes les sessions existantes. Un plan de révocation (ou une coexistence temporaire) est nécessaire lors du passage à la Phase P1.
2. **Locking PostgreSQL** : L'intégration d'une authentification persistante va ajouter des requêtes SQL bloquantes (I/O). FastAPI devra utiliser `asyncpg` systématiquement pour éviter le thread-starvation.
3. **Complexité RBAC vs Web** : Ne jamais exposer les classes Python internes de `core/auth` au web. C'est le rôle de l'API Gateway de transformer une session JWT en un modèle d'autorisation compris par le Core.
