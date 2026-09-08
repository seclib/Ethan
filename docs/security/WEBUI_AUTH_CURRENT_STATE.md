# ETHAN WebUI — État Actuel de l'Authentification

> Diagnostic réalisé le 09/03/2026
> Objectif : évaluer l'architecture existante avant évolution vers l'authentification cryptographique

---

## 1. Résumé Exécutif

ETHAN utilise actuellement une authentification **JWT + bcrypt** classique :

- **Backend** : FastAPI avec `python-jose` (HS256)
- **Session** : Cookie HttpOnly `ethan_token` (SameSite=lax, 24h)
- **Mots de passe** : bcrypt hashés en PostgreSQL
- **WebUI** : Next.js avec proxy API et middleware de redirection
- **RBAC** : 3 rôles (admin/user/viewer) dans `core/auth/__init__.py`

**Problèmes critiques identifiés :**
1. Bootstrap admin avec mot de passe faible (`admin`)
2. Registration publique sans contrôle
3. JWT_SECRET par défaut dans `.env.example`
4. Plusieurs systèmes de permissions concurrents
5. Pas de rate limiting visible sur les routes auth
6. TOTP 2FA optionnel mais non forcé pour l'admin

---

## 2. Architecture Backend

### 2.1 Stack Technologique

| Composant | Technologie | Fichier |
|-----------|-------------|---------|
| Framework | FastAPI | `interfaces/api/main.py` |
| JWT | python-jose[cryptography] (HS256) | `interfaces/api/auth.py` |
| Hash | bcrypt (via passlib) | `interfaces/api/main.py` |
| Base | PostgreSQL (asyncpg) | `deploy/postgres/migrations/003_create_users_table.sql` |
| RBAC | RBACEngine custom | `core/auth/__init__.py` |
| 2FA | TOTP (optionnel) | `core/auth/totp.py` |

### 2.2 Routes d'Authentification

| Route | Méthode | Accès | Description |
|-------|---------|-------|-------------|
| `/auth/login` | POST | Public | Vérifie bcrypt, retourne JWT |
| `/auth/register` | POST | **Public** | Crée user (rôle `user`) |
| `/auth/me` | GET | Protégé | Retourne l'utilisateur courant |
| `/auth/refresh` | POST | Protégé | Renouvelle le JWT |
| `/auth/logout` | POST | Public | Supprime le cookie |

### 2.3 Flux d'Authentification Actuel

```
Utilisateur
    │
    ▼
POST /auth/login { username, password }
    │
    ▼
---

## 3. Architecture WebUI

### 3.1 Composants

| Composant | Fichier | Rôle |
|-----------|---------|------|
| AuthProvider | `providers/auth-provider.tsx` | Contexte React, login/logout/refresh |
| LoginPage | `app/(auth)/login/page.tsx` | Page de connexion |
| LoginForm | `app/(auth)/login/components/login-form.tsx` | Formulaire (operator ID + password) |
| RegisterPage | `app/(auth)/register/page.tsx` | Inscription publique |
| Middleware | `middleware.ts` | Redirection si non authentifié |
| ProxyAPI | `app/api/[...path]/route.ts` | Proxy vers backend |

### 3.2 Flux WebUI

```
Navigateur
    │
    ▼
middleware.ts → vérifie cookie ethan_token
    │
    ├── Pas de cookie → redirige vers /login
    │
    ▼
LoginPage → AuthProvider.login(email, password)
    │
    ▼
POST /api/auth/login → proxy → backend
    │
    ▼
Cookie HttpOnly set par le proxy
    │
    ▼
Redirection vers /
```

---

## 4. Base de Données

### 4.1 Table `users`

```sql
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    roles         TEXT[] NOT NULL DEFAULT '{user}',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.2 Bootstrap Admin (Problème de Sécurité)

La migration `003_create_users_table.sql` crée automatiquement :

```sql
INSERT INTO users (id, username, password_hash, roles)
VALUES (
    'user_admin_00000000',
    'admin',
    '$2b$12$IMasHHKJXSeiAxx6kYiGf.8zkx.ueVl6/oWo61VnT0mGCbv9.CQzK',
    '{admin}'
) ON CONFLICT (username) DO NOTHING;
```

**Mot de passe par défaut : `admin`**

C'est un risque de sécurité majeur si non changé après installation.

---

## 5. Systèmes de Permissions (Problème d'Architecture)

**Plusieurs systèmes concurrents identifiés :**

| Fichier | Classe | Usage |
|---------|--------|-------|
| `core/auth/__init__.py` | `Permission(Enum)`, `RBACEngine` | RBAC principal |
| `core/safety/__init__.py` | `Permission(Enum)` | Safety module |
| `core/modules/permissions.py` | `Permissions`, `PermissionDenied` | Modules |
| `core/security/types.py` | `Permission(Enum)` | Security types |
| `core/security/validation/permissions.py` | `PermissionChecker` | Validation |

**Problème** : il n'y a pas de source de vérité unique pour les permissions. Cela crée des incohérences potentielles.

---

## 6. Analyse des Risques

### 6.1 Risques Critiques

| Risque | Sévérité | Probabilité | Statut |
|--------|----------|-------------|--------|
| Bootstrap admin avec mot de passe faible | **CRITICAL** | Haute | Non corrigé |
| JWT_SECRET par défaut | **HIGH** | Moyenne | `.env.example` seulement |
| Registration publique | **MEDIUM** | Haute | Non corrigé |
| Pas de rate limiting auth | **MEDIUM** | Moyenne | Non corrigé |
| Cookie SameSite=lax (CSRF) | **MEDIUM** | Faible | Non corrigé |

### 6.2 Dépendances Disponibles

```
python-jose[cryptography]>=3.3  → JWT
passlib[bcrypt]>=1.7           → Hash
```

**Pas de WebAuthn/fido2** dans les dépendances.

---

## 7. Conclusion

L'architecture actuelle est **fonctionnelle mais non sécurisée par défaut** :

- ✅ JWT + cookie HttpOnly (bonnes pratiques de base)
- ✅ bcrypt pour les mots de passe
- ✅ RBAC avec rôles
- ✅ TOTP 2FA disponible
- ❌ Bootstrap admin faible
- ❌ Registration publique sans contrôle
- ❌ Pas de rate limiting
- ❌ Systèmes de permissions multiples (confusion)
- ❌ Pas d'authentification cryptographique (WebAuthn/Passkey)

**Prochaine étape** : concevoir l'architecture cible avec WebAuthn/Passkey.

Vérification bcrypt en base (table users)
    │
    ▼
Si TOTP activé → vérification code
    │
    ▼
Création JWT (HS256, 24h)
    │
    ▼
Cookie HttpOnly ethan_token
    │
    ▼
Requêtes suivantes : cookie → Bearer header (proxy Next.js)
```

### 2.4 Middleware d'Authentification

Le middleware ASGI dans `interfaces/api/auth.py` :
1. Vérifie si le chemin est public (`PUBLIC_PATHS`)
2. Lit le cookie `ethan_token` ou le header `Authorization: Bearer`
3. Décode le JWT avec `jwt.decode()`
4. Injecte `request.state.user` et `request.state.token_payload`
5. Retourne 401 si invalide

### 2.5 Proxy WebUI

`interfaces/webui/src/app/api/[...path]/route.ts` :
- Redirige `/api/*` vers le backend (`ETHAN_API_URL`)
- Convertit le cookie `ethan_token` en header `Authorization: Bearer`
- Gère les cookies HttpOnly dans les réponses (login/refresh/logout)
