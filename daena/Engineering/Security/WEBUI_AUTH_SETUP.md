# ETHAN WebUI — Guide de Setup Authentification Cryptographique

> Guide d'installation et de configuration WebAuthn/Passkey
> Date : 09/03/2026

---

## 1. Prérequis

### 1.1 Système

- Node.js 18+
- Python 3.10+
- PostgreSQL 14+
- Redis 6+

### 1.2 Navigateurs Supportés

| Navigateur | Version | WebAuthn | Passkey |
|------------|---------|----------|---------|
| Chrome | 67+ | ✅ | ✅ |
| Firefox | 60+ | ✅ | ✅ |
| Safari | 13+ | ✅ | ✅ |
| Edge | 79+ | ✅ | ✅ |

### 1.3 Authentificateurs Supportés

- **Plateforme** : Touch ID, Windows Hello, Android Biometrics
- **Appareil** : YubiKey 5+, FEITIAN, SoloKeys
- **Hybride** : Phone via QR code (caBLE)

---

## 2. Installation

### 2.1 Dépendances Backend

```bash
# Activer le venv
source .venv/bin/activate

# Installer pywebauthn
pip install "pywebauthn>=2.0"

# Ou ajouter à pyproject.toml
poetry add pywebauthn@^2.0
```

### 2.2 Dépendances Frontend

Aucune dépendance supplémentaire nécessaire — WebAuthn est natif dans les navigateurs.

### 2.3 Configuration Environnement

```bash
# .env

# WebAuthn Configuration
WEBAUTHN_RP_ID=ethan.local
WEBAUTHN_RP_NAME=ETHAN
WEBAUTHN_ORIGIN=https://ethan.local
WEBAUTHN_CHALLENGE_TTL=60

# Optionnel : pour développement local
# WEBAUTHN_ORIGIN=http://localhost:3000
```

---

## 3. Configuration

### 3.1 Reverse Proxy / TLS

**WebAuthn nécessite HTTPS en production.**

```nginx
# nginx.conf (extrait)
server {
    listen 443 ssl http2;
    server_name ethan.local;

    ssl_certificate /etc/ssl/ethan.crt;
    ssl_certificate_key /etc/ssl/ethan.key;

    location / {
        proxy_pass http://webui:3000;
    }

    location /api {
        proxy_pass http://api:8000;
    }
}
```

**Développement local** : HTTP fonctionne sur `localhost`.

### 3.2 CORS

```python
# Configuration CORS pour l'API
ALLOWED_ORIGINS = [
    "https://ethan.local",
    # "http://localhost:3000",  # dev uniquement
]
```

### 3.3 Session

```python
# Configuration JWT (existant)
JWT_SECRET=votre-secret-securise-ici  # openssl rand -base64 64
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
```

---

## 4. Bootstrap Admin

### 4.1 Premier Démarrage

**Problème** : comment créer le premier admin sans login existant ?

**Solution** : Bootstrap via CLI ou variable d'environnement.

#### Option A : Bootstrap CLI

```bash
# Créer un admin avec WebAuthn
---

## 6. Sécurité en Production

### 6.1 Checklist

- [ ] HTTPS activé (TLS 1.2+)
- [ ] Certificat SSL valide
- [ ] WEBAUTHN_RP_ID configuré
- [ ] WEBAUTHN_ORIGIN configuré
- [ ] CORS restrictif
- [ ] Rate limiting activé
- [ ] Audit logging activé
- [ ] Session timeout configuré
- [ ] Backup credentials plan B
- [ ] Monitoring des échecs d'authentification

### 6.2 Monitoring

Surveiller :
- Taux d'échec d'authentification
- Taux d'échec d'enregistrement
- Utilisateurs bloqués
- Erreurs de validation de signature
- Challenges expirés (potentielle attaque)

### 6.3 Backup et Recovery

**Perte de la credential WebAuthn** :

1. **Codes de récupération** : Générer à l'enregistrement
2. **Credential secondaire** : Enregistrer 2+ credentials
3. **Mot de passe fallback** : Conserver le mot de passe en backup
4. **Admin recovery** : Un admin peut réinitialiser les credentials d'un utilisateur

⚠️ **Ne pas implémenter de recovery par email sans analyse de sécurité** (risque de takeover).

---

## 7. Développement et Tests

### 7.1 Tests Locaux

```bash
# Lancer les tests d'authentification
pytest tests/test_auth_webauthn.py -v

# Tests d'intégration
pytest tests/test_auth_integration.py -v
```

### 7.2 Simulateur WebAuthn

Pour les tests automatisés, pywebauthn fournit des utilitaires de test.

### 7.3 CI/CD

```yaml
# .github/workflows/auth-tests.yml
name: Auth Security Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run auth tests
        run: |
          pip install -e ".[test]"
          pytest tests/test_auth_webauthn.py -v
```

---

## 8. Dépannage

### 8.1 Problèmes Courants

| Problème | Cause | Solution |
|----------|-------|----------|
| "WebAuthn non supporté" | HTTP au lieu de HTTPS | Utiliser HTTPS |
| "RP ID mismatch" | Mauvaise config | Vérifier WEBAUTHN_RP_ID |
| "Challenge expiré" | Trop lent | Augmenter TTL ou recommencer |
| "Credential inconnue" | Supprimée | Ré-enregistrer |
| "Signature invalide" | Clock sync | Synchroniser l'heure |

### 8.2 Logs

```bash
# Logs d'authentification
docker compose logs api | grep -i "auth\|webauthn\|login\|register"

# Logs d'erreur
docker compose logs api | grep -i "error\|fail\|reject"
```

---

## 9. Architecture Future

Cette implémentation WebAuthn est compatible avec l'évolution future :

- **Human Root of Trust** : la credential WebAuthn devient la racine de confiance
- **Action Authorization** : signer des actions critiques avec la credential
- **Agent Identity** : les agents peuvent avoir des credentials distinctes
- **Multi-sig** : nécessiter plusieurs credentials pour les actions sensibles

---

## 10. Ressources

### 10.1 Documentation

- [WebAuthn Spec (W3C)](https://www.w3.org/TR/webauthn-2/)
- [pywebauthn Docs](https://duo.github.io/pywebauthn/)
- [FIDO Alliance](https://fidoalliance.org/)

### 10.2 Outils

- [WebAuthn.io](https://webauthn.io/) — Démo interactive
- [WebAuthn Debugger](https://webauthn.debugger.io/) — Debugging

---

## 11. Résumé

| Étape | Action |
|-------|--------|
| 1 | Installer pywebauthn |
| 2 | Configurer WEBAUTHN_RP_ID, WEBAUTHN_ORIGIN |
| 3 | Ajouter les endpoints API |
| 4 | Ajouter le frontend WebAuthn |
| 5 | Bootstrap admin |
| 6 | Tester en local |
| 7 | Déployer en production avec HTTPS |
| 8 | Monitorer |

ethan admin create --username admin

# Output :
# 🔐 WebAuthn Registration Challenge
# → Ouvrez https://ethan.local/register
# → Branchez votre YubiKey ou utilisez Touch ID
# → Credential enregistrée avec succès
```

#### Option B : Bootstrap par Token Temporaire

```bash
# Premier démarrage : génère un token temporaire
docker compose up api

# Log :
# [ETHAN] First boot detected. Temporary admin token:
# [ETHAN] ETHAN_ADMIN_TOKEN=eyJhbGciOiJIUzI1NiIs...
# [ETHAN] Token expires in 1 hour.

# Utiliser le token pour se connecter et enregistrer WebAuthn
```

#### Option C : Variable d'Environnement (CI/CD)

```bash
# Dans .env
ETHAN_ADMIN_USERNAME=admin
ETHAN_ADMIN_TEMPORARY_PASSWORD=changeme-immediately
```

⚠️ **Changer le mot de passe temporaire immédiatement après le premier login.**

### 4.2 Migration depuis un Système Existant

```bash
# Les utilisateurs existants peuvent :
# 1. Se connecter avec mot de passe + TOTP
# 2. Ajouter une credential WebAuthn dans les settings
# 3. Supprimer le mot de passe (optionnel)

ethan migrate-to-webauthn --username developer
```

---

## 5. Utilisation

### 5.1 Enregistrement d'une Credential

1. Se connecter avec mot de passe (première fois)
2. Aller dans **Settings > Security > WebAuthn Credentials**
3. Cliquer sur **"Add Credential"**
4. Suivre les instructions du navigateur (YubiKey/Touch ID)
5. Donner un nom à la credential (ex: "Ma YubiKey")
6. Credential enregistrée

### 5.2 Connexion avec WebAuthn

1. Aller sur la page de login
2. Cliquer sur **"🔐 Se connecter avec WebAuthn"**
3. Entrer son username
4. Suivre les instructions du navigateur
5. Authentifié — redirection vers le dashboard

### 5.3 Gestion des Credentials

- **Liste** : Voir toutes ses credentials
- **Rename** : Changer le nom d'une credential
- **Delete** : Supprimer une credential
- **Require** : Imposer WebAuthn pour son compte
