# Audit des Systèmes d'Authentification (ETHAN OS)

Cet audit a pour but d'identifier les différents systèmes d'authentification concurrents ou superposés dans l'écosystème ETHAN, afin de clarifier la chaîne de confiance.

---

## 1. Réponses aux questions d'architecture

1. **Combien de systèmes utilisateur existent ?**
   Il existe **2 systèmes distincts** (hors projets d'exemples Jarvis) :
   - Un système de **JWT asymétrique / mock** dans `interfaces/api/auth.py` (utilisé activement par l'API Web).
   - Un système **RBAC / API Keys en mémoire** complet dans `core/auth/__init__.py` (héritage de Jarvis OS, actuellement déconnecté de l'API web).

2. **Existe-t-il un AuthManager mémoire ?**
   **Oui.** Dans `core/auth/__init__.py`, on trouve la classe `AuthSystem` (`self._users`, `self._roles`, `self._api_keys`) qui stocke les permissions et rôles dans la RAM du processus Python.

3. **Existe-t-il une authentification PostgreSQL ?**
   **Non.** L'audit des modèles de données et schémas SQL montre qu'il n'existe aucune table de gestion des comptes (ni `users`, ni `accounts`, ni `sessions`). La vérification d'identité est actuellement "permissive" (mock).

4. **Le frontend utilise quel système ?**
   Le frontend WebUI s'appuie sur le système **JWT via Cookie `HttpOnly`**. Il exploite le cookie `ethan_token` pour le routage et un contexte React (`AuthProvider`) qui interroge `/api/auth/me`.

5. **Le backend login utilise quel système ?**
   La route `POST /auth/login` (dans `interfaces/api/main.py`) utilise la fonction `create_access_token()` définie dans `interfaces/api/auth.py`. Elle ne s'interface **pas** avec `core/auth/__init__.py`. 

6. **Le middleware Next utilise quel système ?**
   Le fichier `middleware.ts` utilise un système de **Vérification de Présence**. Il se contente de vérifier si le cookie `ethan_token` existe dans la requête, sans valider la signature cryptographique du JWT (qui est de toute façon validée plus tard par l'API backend).

7. **Le dashboard utilise quel système ?**
   Le Dashboard est protégé côté client par le composant `AuthProvider`, qui appelle `GET /api/auth/me`. Ce endpoint backend utilise le middleware FastAPI (`auth_middleware` de `interfaces/api/auth.py`) pour déchiffrer et valider cryptographiquement le JWT.

---

## 2. Traçabilité du Flux d'Authentification

```text
[Utilisateur]
      ↓
[Formulaire /login (Next.js)] 
      ↓ (fetch POST /api/auth/login)
[Proxy Manuel (Route Handler)]
      ↓ (HTTP POST /auth/login)
[Validation FastAPI] -> (Mock : Accepte les credentials par défaut -> username)
      ↓
[Création Session] -> (Génération JWT HS256)
      ↓
[Stockage Token] -> (FastAPI set_cookie -> Route Handler relaie -> Navigateur stocke cookie HttpOnly)
      ↓
[Navigation window.location.href = "/"]
      ↓
[Middleware Next.js] -> (Vérifie présence cookie "ethan_token", autorise)
      ↓
[Dashboard] -> (AuthProvider fetch GET /api/auth/me -> FastAPI valide signature JWT -> UI affiche contenu)
```

---

## 3. Analyse des Doublons (Dette Technique)

1. **Doublon de logique Auth Backend** :
   - `core/auth/__init__.py` : Code très avancé pour les permissions et les clés d'API (probablement utile pour les SDKs de l'OS).
   - `interfaces/api/auth.py` : Code simplifié pour la connexion par mot de passe / JWT.
   *-> Les deux ne sont pas reliés.*

2. **Doublon Frontend (Session & LocalStorage)** :
   - L'authentification a bien été migrée pour utiliser le cookie sécurisé `ethan_token`.
   - Néanmoins, on trouve encore des traces d'écritures pour un "pseudo-cookie" client : `localStorage.setItem("ethan_operator_id", operatorId)` qui fait doublon avec l'information d'identité cryptée dans le JWT de session.

3. **Absence de Source de Vérité (DB)** :
   - Le système génère un JWT pour n'importe quel `username` donné car aucune base de données utilisateur n'existe encore. La sécurité actuelle repose donc exclusivement sur le fait de limiter l'accès du portail web.
