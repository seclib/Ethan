# ETHAN WebUI — Architecture d'Authentification Cryptographique

> Architecture cible : WebAuthn / Passkey
> Statut : Conception
> Date : 09/03/2026

---

## 1. Choix Technologique : WebAuthn / Passkey

### 1.1 Pourquoi WebAuthn ?

| Critère | WebAuthn | Challenge-Response Custom | TOTP 2FA |
|---------|----------|---------------------------|----------|
| Standard W3C | ✅ Oui | ❌ Non | ❌ Non |
| Résistant au phishing | ✅ Oui | ❌ Dépend | ❌ Non |
| Clé privée jamais transmise | ✅ Oui | ✅ Oui | N/A |
| Support navigateur | ✅ Universel | ✅ Universel | ✅ Universel |
| Bibliothèque serveur mature | ✅ pywebauthn | ❌ Custom | ✅ pyotp |
| Authentificateur externe | ✅ YubiKey | ❌ Non | ✅ Oui |
| Intégration OS | ✅ TouchID/Hello | ❌ Non | ❌ Non |

**Décision** : WebAuthn est le choix standard pour une authentification cryptographique moderne, sans mot de passe, résistante au phishing.

### 1.2 Bibliothèque Serveur : `pywebauthn`

```
pywebauthn>=2.0
```

- Maintenue activement
- Supporte FIDO2/WebAuthn
- Gère registration + verification
- Gère RP ID, origin, challenge, attestation

### 1.3 API Navigateur : Native

```javascript
// Registration
navigator.credentials.create({ publicKey: options })

// Authentication
navigator.credentials.get({ publicKey: options })
```

Aucune bibliothèque frontend nécessaire.

---

## 2. Architecture Cible

### 2.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        NAVIGATEUR                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  WebUI ETHAN                                              │  │
│  │  navigator.credentials.create() / .get()                  │  │
│  │  → clé privée stockée dans l'authentificateur            │  │
│  │  → signature du challenge envoyée au serveur             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTPS ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ETHAN BACKEND (FastAPI)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  WebAuthn Router                                          │  │
│  │  POST /auth/webauthn/register/options                     │  │
│  │  POST /auth/webauthn/register/verify                      │  │
│  │  POST /auth/webauthn/login/options                        │  │
│  │  POST /auth/webauthn/login/verify                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ▼
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  WebAuthnService (pywebauthn)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ▼
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL (table user_credentials)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Flux d'Authentification

```
Utilisateur
    │
    ▼
POST /auth/webauthn/login/options { username }
    │
    ▼
Serveur génère challenge (aléatoire, 32 bytes)
---

## 3. Modèle de Données

### 3.1 Nouvelle Table `user_credentials`

```sql
CREATE TABLE IF NOT EXISTS user_credentials (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credential_id   BYTEA NOT NULL UNIQUE,
    public_key      BYTEA NOT NULL,
    sign_count      INTEGER NOT NULL DEFAULT 0,
    credential_type TEXT NOT NULL DEFAULT 'public-key',
    transports      TEXT[] DEFAULT '{}',
    device_name     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_user_credentials_user_id ON user_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credentials_credential_id ON user_credentials(credential_id);
```

### 3.2 Relations

```
users (1) ──────── (N) user_credentials
   │
   └── Un utilisateur peut avoir plusieurs credentials
       (ex: YubiKey + TouchID + Passkey cloud)
```

---

## 4. Sécurité

### 4.1 Protection contre les Replays

| Mécanisme | Implémentation |
|-----------|----------------|
| Challenge unique | 32 bytes aléatoires (secrets.token_bytes) |
| Expiration | 60 secondes max |
| Single-use | Challenge invalidé après utilisation |
| Sign count | Incrémenté à chaque utilisation, détecte le clonage |
| Origin validation | Vérifié par pywebauthn |
| RP ID | Doit correspondre au domaine |

### 4.2 Stockage

| Donnée | Stockée | Jamais stockée |
|--------|---------|----------------|
| Clé publique | ✅ Oui | — |
| Credential ID | ✅ Oui | — |
| Sign count | ✅ Oui | — |
| **Clé privée** | — | **❌ Jamais** |
| **Secret** | — | **❌ Jamais** |

### 4.3 Session Post-Authentification

Après authentification WebAuthn réussie :
- Un JWT classique est émis (même mécanisme qu'actuellement)
- Cookie HttpOnly `ethan_token`
- La session est **indépendante** de la credential WebAuthn
- La credential prouve l'identité, la session maintient l'état

### 4.4 CORS et Origin

```python
# Seules les origins autorisées peuvent initier WebAuthn
ALLOWED_ORIGINS = [
    "https://ethan.local",
    "https://app.ethan.ai",
]
```

---

## 5. Bootstrap Admin Sécurisé

### 5.1 Problème Actuel

Le mot de passe `admin` par défaut dans la migration SQL est un risque critique.

### 5.2 Solution Proposée

**Option A : Bootstrap par variable d'environnement (recommandée)**

```bash
# .env (production)
ETHAN_ADMIN_USERNAME=admin
ETHAN_ADMIN_WEBAUTHN_CREDENTIAL_ID=...
ETHAN_ADMIN_WEBAUTHN_PUBLIC_KEY=...
```

**Option B : Bootstrap CLI**

```bash
ethan admin create --webauthn
# → Génère un challenge d'enregistrement
# → L'utilisateur branche sa YubiKey / utilise TouchID
# → Credential stocké en base
```

**Option C : Premier démarrage avec token temporaire**

```bash
# Au premier démarrage, si aucun admin n'existe :
# → Générer un token temporaire (valide 1h, affiché dans les logs)
# → L'utilisateur se connecte avec ce token
# → Enregistrement WebAuthn obligatoire avant expiration
```

### 5.3 Migration depuis le Système Actuel

1. La table `users` conserve `password_hash` (compatibilité)
2. Nouvelle table `user_credentials` ajoutée
3. Les utilisateurs existants peuvent :
   - Continuer à utiliser mot de passe + TOTP
   - Ajouter une credential WebAuthn
4. À terme, possibilité de désactiver le mot de passe pour les utilisateurs WebAuthn

---

## 6. Compatibilité et Migration

### 6.1 Coexistence des Méthodes

| Méthode | Statut | Usage |
|---------|--------|-------|
| Mot de passe + bcrypt | ✅ Existant | Compatibilité, fallback |
| TOTP 2FA | ✅ Existant | 2FA optionnel |
| WebAuthn / Passkey | 🆕 Nouveau | Méthode principale |

### 6.2 Stratégie de Migration

**Phase 1** : Ajout WebAuthn en parallèle (pas de rupture)
**Phase 2** : Incitation à utiliser WebAuthn
**Phase 3** : Possibilité de désactiver mot de passe pour utilisateurs WebAuthn
**Phase 4** : WebAuthn uniquement (optionnel)

---

## 7. API Endpoints

| Route | Méthode | Description |
|-------|---------|-------------|
| `/auth/webauthn/register/options` | POST | Options pour enregistrer une credential |
| `/auth/webauthn/register/verify` | POST | Vérifie et stocke la credential |
| `/auth/webauthn/login/options` | POST | Options pour l'authentification |
| `/auth/webauthn/login/verify` | POST | Vérifie l'authentification |
| `/auth/webauthn/credentials` | GET | Liste les credentials de l'utilisateur |
| `/auth/webauthn/credentials/{id}` | DELETE | Supprime une credential |

---

## 8. Dépendances à Ajouter

### 8.1 Backend (pyproject.toml)

```toml
"pywebauthn>=2.0",
```

### 8.2 Frontend

Aucune dépendance — API WebAuthn native dans les navigateurs.

---

## 9. Tests Requis

### 9.1 Tests Unitaires

- Génération des options de registration
- Vérification de la réponse de registration
- Génération des options d'authentification
- Vérification de la réponse d'authentification
- Validation du sign_count
- Rejet des challenges expirés

### 9.2 Tests d'Intégration

- Flux complet de registration
- Flux complet d'authentification
- Rejet d'une credential inconnue
- Rejet d'une signature invalide
- Rejet d'un challenge réutilisé
- Mauvaise origin
- Mauvais RP ID

### 9.3 Tests de Sécurité

- Clé privée jamais reçue par le backend
- Clé privée jamais stockée en base
- Clé privée absente des logs
- Impossible de créer un admin sans credential valide
- Impossible de réutiliser une ancienne assertion

---

## 10. Résumé

| Aspect | Détail |
|--------|--------|
| Protocole | WebAuthn / Passkey (FIDO2) |
| Bibliothèque serveur | pywebauthn |
| API navigateur | Native (navigator.credentials) |
| Stockage serveur | Clé publique + credential ID |
| Clé privée | **Jamais** sur le serveur |
| Session | JWT classique post-auth |
| Migration | Coexistence avec mot de passe |
| Bootstrap admin | CLI ou token temporaire |

    │
    ▼
Retourne { challenge, allowCredentials, rpId, timeout }
    │
    ▼
navigator.credentials.get({ publicKey: options })
    │
    ▼
Authentificateur signe challenge avec clé privée
    │
    ▼
POST /auth/webauthn/login/verify { credential }
    │
    ▼
Serveur vérifie signature avec clé publique stockée
    │
    ▼
Vérifie sign_count (replay protection)
    │
    ▼
Crée session JWT (cookie HttpOnly)
    │
    ▼
Utilisateur authentifié
```

### 2.3 Flux d'Enregistrement

```
Utilisateur (déjà authentifié ou admin)
    │
    ▼
POST /auth/webauthn/register/options { username }
    │
    ▼
Serveur génère challenge + user info
    │
    ▼
Retourne { challenge, user, rp, pubKeyCredParams, timeout }
    │
    ▼
navigator.credentials.create({ publicKey: options })
    │
    ▼
Authentificateur génère paire de clés
    │
    ▼
POST /auth/webauthn/register/verify { credential }
    │
    ▼
Serveur vérifie attestation
    │
    ▼
Stocke { credential_id, public_key, sign_count }
    │
    ▼
Credential enregistrée
```
