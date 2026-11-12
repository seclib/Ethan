# ETHAN WebUI — Modèle de Menace Authentification

> Threat Model pour l'authentification WebAuthn
> Date : 09/03/2026

---

## 1. Acteurs

### 1.1 Utilisateurs Légitimes

| Acteur | Description | Niveau de confiance |
|--------|-------------|---------------------|
| Admin | Administrateur ETHAN | Élevé |
| User | Utilisateur standard | Moyen |
| Viewer | Utilisateur lecture seule | Moyen |

### 1.2 Attaquants Potentiels

| Acteur | Description | Capacité |
|--------|-------------|----------|
| Remote Attacker | Attaquant distant, non authentifié | Réseau |
| Phishing Attacker | Attaquant avec page de login falsifiée | Social Engineering |
| Malware Attacker | Attaquant avec accès au poste utilisateur | Local |
| Insider Attacker | Utilisateur authentifié malveillant | Interne |
| Supply Chain | Compromission de dépendance | Code |

---

## 2. Surface d'Attaque

### 2.1 Points d'Entrée

| Point d'Entrée | Exposition | Méthode d'Attaque |
|----------------|------------|-------------------|
| `/auth/webauthn/login/options` | Public | Force brute, énumération |
| `/auth/webauthn/login/verify` | Public | Replay, forgery |
| `/auth/webauthn/register/options` | Protégé | CSRF, fuite d'info |
| `/auth/webauthn/register/verify` | Protégé | Forgery |
| `/auth/login` (legacy) | Public | Force brute, credential stuffing |
| Cookie `ethan_token` | Navigateur | XSS, CSRF, vol |
| Base de données | Interne | SQL injection, exfiltration |

### 2.2 Flux de Données Sensibles

```
Navigateur ──challenge──→ Backend (séparé, pas de clé privée)
Backend ──options────→ Navigateur
Navigateur ──signature──→ Backend (vérification)
Backend ──JWT────────→ Cookie HttpOnly
```

---

## 3. Menaces Identifiées

### 3.1 Authentification

| ID | Menace | Sévérité | Probabilité | Mitigation |
|----|--------|----------|-------------|------------|
| T01 | Challenge replay | Élevée | Faible | Expiration 60s, single-use |
| T02 | Signature forgery | Critique | Très faible | Cryptographie WebAuthn |
| T03 | Brute force username | Moyenne | Moyenne | Rate limiting, énumération |
| T04 | Credential stuffing | Moyenne | Faible | WebAuthn résistant (pas de mot de passe) |
| T05 | Phishing | Moyenne | Moyenne | WebAuthn résistant (RP ID) |
| T06 | Man-in-the-middle | Critique | Faible | HTTPS obligatoire |

### 3.2 Session

| ID | Menace | Sévérité | Probabilité | Mitigation |
|----|--------|----------|-------------|------------|
| T07 | Vol de cookie | Élevée | Faible | HttpOnly, Secure, SameSite |
| T08 | CSRF | Moyenne | Faible | SameSite=lax, tokens CSRF |
| T09 | Session fixation | Moyenne | Faible | Nouveau token après login |
| T10 | JWT theft | Élevée | Faible | Expiration courte, rotation |

### 3.3 Enregistrement

| ID | Menace | Sévérité | Probabilité | Mitigation |
---

## 4. Scénarios d'Attaque Détaillés

### 4.1 S01 : Phishing avec Page de Login Falsifiée

**Description** : L'attaquant crée une page de login ETHAN falsifiée.

**Flux** :
1. L'utilisateur visite `https://ethan-login.fake`
2. La page demande une credential WebAuthn
3. `navigator.credentials.get()` échoue car RP ID ≠ domaine légitime

**Résultat** : **BLOQUÉ** — WebAuthn vérifie le RP ID (domaine).

**Mitigation** :
- Le navigateur refuse les credentials pour un RP ID différent
- L'utilisateur ne peut pas être piégé

### 4.2 S02 : Replay d'un Challenge

**Description** : L'attaquant capture une tentative de login et la rejoue.

**Flux** :
1. L'attaquant capture `{ challenge, credential, signature }`
2. L'attaquant rejoue la même requête
3. Le serveur détecte le challenge déjà utilisé ou expiré

**Résultat** : **BLOQUÉ** — Challenge single-use + expiration 60s.

**Mitigation** :
- Challenges stockés en Redis avec TTL 60s
- Après utilisation, le challenge est supprimé
- Le sign_count empêche aussi le replay

### 4.3 S03 : Vol de Cookie par XSS

**Description** : L'attaquant injecte du JavaScript pour voler le cookie.

**Flux** :
1. XSS dans la WebUI
2. `document.cookie` → impossible (HttpOnly)
3. L'attaquant utilise le cookie indirectement via fetch()

**Résultat** : **PARTIELLEMENT BLOQUÉ** — HttpOnly empêche le vol direct.

**Mitigation** :
- HttpOnly cookie
- Content Security Policy (CSP)
- X-XSS-Protection
- Validation des inputs

### 4.4 S04 : Enregistrement Non Autorisé

**Description** : L'attaquant tente d'enregistrer une credential pour un autre utilisateur.

**Flux** :
1. L'attaquant trouve un moyen d'appeler `/auth/webauthn/register/options`
2. Il génère un challenge pour `admin`
3. Il enregistre sa propre credential

**Résultat** : **BLOQUÉ** — L'enregistrement nécessite une session valide.

**Mitigation** :
- `/auth/webauthn/register/*` nécessite une session JWT valide
- Un utilisateur ne peut enregistrer des credentials que pour lui-même
- L'admin peut enregistrer pour d'autres (avec audit)

### 4.5 S05 : Compromission du Navigateur

**Description** : L'attaquant a accès au poste utilisateur.

**Flux** :
1. L'attaquant ouvre la WebUI
2. WebAuthn demande la credential
3. Si l'utilisateur a laissé sa session active → accès

**Résultat** : **RISQUE** — WebAuthn ne protège pas contre l'accès physique.

**Mitigation** :
- Timeout de session court
- Verrouillage automatique
- 2FA pour les actions sensibles
- Notification d'activité suspecte

---

## 5. Modèle de Confiance

### 5.1 Niveaux de Confiance

```
┌─────────────────────────────────────────────────────────────┐
│                    HOSTILE (niveau 0)                        │
│  Sources externes non vérifiées                              │
├─────────────────────────────────────────────────────────────┤
│                    UNTRUSTED (niveau 1)                      │
│  Utilisateurs anonymes, endpoints publics                   │
├─────────────────────────────────────────────────────────────┤
│                    REVIEWED (niveau 2)                       │
│  Utilisateurs authentifiés par mot de passe                │
├─────────────────────────────────────────────────────────────┤
│                    USER_APPROVED (niveau 3)                  │
│  Utilisateurs authentifiés par WebAuthn                    │
├─────────────────────────────────────────────────────────────┤
│                    TRUSTED (niveau 4)                        │
│  Admin avec WebAuthn + TOTP                                │
├─────────────────────────────────────────────────────────────┤
│                    SYSTEM (niveau 5)                         │
│  Composants internes ETHAN                                 │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Frontières de Confiance

| Frontière | Protection |
|-----------|------------|
| Navigateur ↔ Backend | HTTPS, CORS, origin validation |
| WebUI ↔ API | Proxy avec cookie → Bearer |
| API ↔ Base de données | Paramétré, moindre privilège |
| Backend ↔ Challenge store | Redis avec TTL |

---

## 6. Exigences de Sécurité

### 6.1 DO (Obligatoire)

- HTTPS en production
- HttpOnly + Secure + SameSite cookies
- Challenges à usage unique avec expiration
- Validation du sign_count
- Rate limiting sur endpoints auth
- Audit logging des événements d'authentification
- Validation de l'origin et du RP ID

### 6.2 DON'T (Interdit)

- Clé privée sur le serveur
- Stockage de secrets en clair
- Challenges persistants sans expiration
- Registration sans authentification préalable
- CORS wildcards (`*`) en production
- Logging de données sensibles

---

## 7. Conclusion

WebAuthn offre une protection supérieure aux mots de passe :

- **Résistant au phishing** (RP ID binding)
- **Pas de secrets partagés** (clé privée jamais transmise)
- **Pas de credential stuffing** (pas de mot de passe)
- **Replay protection** (challenge unique + sign_count)

Les risques résiduels sont :
- Accès physique au poste utilisateur
- Compromission du navigateur
- Supply chain attacks sur les dépendances

Ces risques sont acceptés et couverts par des mesures complémentaires (CSP, audit, rotation).

|----|--------|----------|-------------|------------|
| T11 | Enregistrement non autorisé | Critique | Faible | Auth requise pour register |
| T12 | Credential clonage | Élevée | Très faible | Sign count |
| T13 | Attestation forgery | Élevée | Très faible | Vérification attestation |
| T14 | Registration CSRF | Moyenne | Faible | Vérification session |

### 3.4 Infrastructure

| ID | Menace | Sévérité | Probabilité | Mitigation |
|----|--------|----------|-------------|------------|
| T15 | Fuite de clés publiques | Moyenne | Faible | Pas de données sensibles |
| T16 | Compromission base de données | Élevée | Faible | Pas de secrets stockés |
| T17 | Compromission serveur | Critique | Très faible | HSM, key rotation |
| T18 | Supply chain attack | Élevée | Faible | Audit dépendances |
