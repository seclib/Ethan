# WebUI ETHAN — Validation du port officiel 3001

> **Status : PASS** — ETHAN WebUI fonctionne réellement sur `http://localhost:3001`.
> **Date** : 27 août 2026.

---

## 1. Processus qui occupait 3001

Le port 3001 était occupé par un **container Docker `ethan-ui`** (service UI du
`docker-compose` racine du projet ETHAN).

| Élément | Valeur |
|---|---|
| Container | `ethan-ui` (projet `ethan`) |
| Image | `ethan-ui` (built local, cached) |
| Mapping | `127.0.0.1:3001->3000/tcp` |
| Statut (avant) | `Up 6 hours (healthy)` |
| CPU root | `next-server (v15.5.23)` au sein du container (`npm run start` → conteneur-shim) |

## 2. Origine du processus

Ce **n'était PAS un processus local orphelin/abandonné** (`npm run dev` root), mais
le **container Docker officiel du service UI** de la stack ETHAN. Diagnose :

- `ss -ltnp` → `LISTEN 127.0.0.1:3001` (sans PID lisible pour l'utilisateur non-root)
- `ps` → `next-server (v15.5.23)` enfant de `npm run start` enfant de
  `containerd-shim-runc-v2 … -id e2b5ea370430b0d5ba4a8025c6baa5860790ed353a4403d65… -namespace moby`
- `docker ps` → `e2b5ea370430 ethan-ui … 127.0.0.1:3001->3000/tcp Up 6 hours`

Il servait un **build de 6h**, **antérieur** à la refonte visuelle (`globals.css`,
tokens neutres + Inter). Il fallait donc le libérer pour servir le **nouveau** build.

## 3. Méthode utilisée pour le stopper

Arrêt propre via l'outil conteneur (pas de `kill -9` ni de privilège root) :

```bash
docker stop ethan-ui
```

Résultat : `ethan-ui Exited (0)` ; le port 3001 est devenu libre. (Le container reste
présent et rechargeable ; il n'est pas supprimé.)

## 4. État final du port 3001

`ss -ltn | grep 3001` → `LISTEN 0 511 *:3001 *:*` — écouté par le serveur de dev ETHAN.

## 5. Commande utilisée pour lancer ETHAN WebUI

```bash
./ethan webui
```
(passe par `scripts/cmd-webui.sh`, `PORT=${PORT:-3001}`, lance Next.js en mode
développement sur le port **3001**.)

Résultat du lancement :
```
✓ API déjà disponible sur http://localhost:8000
  ℹ Mode développement sur http://localhost:3001
  ▲ Next.js 15.5.23
  - Local:        http://localhost:3001
  ✓ Ready in 2.1s
```

## 6. URL finale

```
http://localhost:3001
```

## 7. Résultat HTTP

| Route | Résultat | Sens |
|---|---|---|
| `GET /` | **307** | Redirection middleware vers `/login` (pas de session) — attendu |
| `GET /login` | **200** | Page de connexion servant le layout |
| `GET /workspace` | **307** | Page protégée → redirection auth sans cookie — attendu |
| `GET /api/v1/settings` (via 3001) | **401** | Proxy Next → API :8000 atteinte (auth requise) |
| `GET :8000/health/ready` | **200** | API backend up |

## 8. Résultat navigateur

Le layout est rendu : on retrouve dans le DOM serve PAR 3001 des classes telles que
`app-header`, `app-header-crumb`, `app-header-page`, presets thème.

## 9. Résultat du nouveau CSS

Le fichier `/_next/static/css/app/layout.css` servi par **:3001** contient les tokens
de la refonte Open-WebUI-like :

- `--bg-rgb: 23 23 27` (dark), `250 250 252` (light)
- `--surface-elevated-rgb: 31 31 37` (dark), `255 255 255` (light)
- `font-family: …'Inter'…` (base sans-serif)
- `border-radius:20px` (chat-input)

Soit exactement le nouvel enveloppe visuelle — confirme que le build servi est le
**nouveau**, pas un cache pré-refonte.

## 10. Aucune configuration 3011 résiduelle

Recherche `3011` dans le projet (excluant `node_modules`, `.next`, et le rapport
lui-même) :
```
(grep) → aucun résultat
```
Le port temporaire **3011** n'apparaît nulle part comme référence durable. Le
répertoire de référence officielle reste **3001** (`scripts/cmd-webui.sh`,
`interfaces/webui/webui.sh`, `scripts/cmd-status.sh`, `docker-compose.yml`).

---

## Chaîne complète validée

```
Navigateur
   ↓
http://localhost:3001 (ETHAN WebUI — Next.js 15 / refonte Open-WebUI)
   ↓  /api/*
Node.js proxy → FastAPI backend :8000 (container ethan-api)
   ↓
ETHAN Core / Runtime
```

## Note d'hygiène

Le container `ethan-ui` reste dans `docker ps -a` en état `Exited (0)`, volontairement
non supprimé. Pour revenir au rendu Docker (mode prod), on pourra le redémarrer après
reconstruire son image :

```bash
./ethan up                  # reconstruit + relance la stack (dont UI sur 3001)
```

---

## Re-validation finale (2e blocage signalé)

### Diagnostic définitif de l'occupation de 3001

| Question | Réponse vérifiée |
|---|---|
| Processus | next-server **interne au conteneur Docker `ethan-ui`** (PID root, parent containerd) |
| Origine | **Stack systemd officielle ETHAN** : `ethan-core.service` (stack compose) + `ethan-runtime.service` (Docker Controller) + `ethan-watchdog.timer` (30s) |
| Pourquoi il « revient » | Policy `unless-stopped` + contrôleur root : un `docker stop` est suivi d'une recréation par la stack — comportement **voulu**, pas un processus orphelin |
| Libération sans root ? | **Non.** Arrêt définitif nécessite sudo (commandes ci-dessous) |

### Décision : validation via le chemin de production officiel

L'image `ethan-ui:latest` a été **reconstruite depuis le source actuel** (36 min) — le conteneur officiel sur 3001 sert donc la **dernière WebUI** :

```
./ethan up (stack systemd officielle) → ethan-ui : 127.0.0.1:3001 → WebUI dernière version → /api/* → ETHAN API :8000
```

### Preuves (port 3001, conteneur officiel, build actuel)

| Vérification | Résultat |
|---|---|
| Image | `ethan-ui:latest` — 36 min, sha `4839d9c33653` = image du conteneur courant |
| Conteneur | `Up (healthy)`, `127.0.0.1:3001->3000/tcp` |
| Nav v3 SSR `/workspace` | `>Explore<` `>Pilotage<` `>Settings<` `>Administration<` ✓ |
| Page `/diagnostics` | 200 — « Santé des services », « Actualiser » ✓ |
| CSS servi | `Inter`, `--sidebar-bg`, `--bg-rgb:23 23 27` (dark neutre OWUI) ✓ |
| 19 routes | **toutes 200** (`/` `/login` `/register` `/agents` `/models` `/skills` `/knowledge` `/tools` `/providers` `/settings` `/workspace` `/missions` `/calendar` `/notes` `/inbox` `/research` `/cookbook` `/security` `/diagnostics`) |
| API backend | `:8000/health` = 200 ; proxy `:3001/api/v1/settings` = 401 (auth requise, backend atteint) ✓ |
| Références 3011 | **aucune** dans src/, scripts/, configs ✓ |

### Port 3001 en mode dev hôte (optionnel, à exécuter par l'utilisateur)

```bash
sudo systemctl stop ethan-runtime.service ethan-core.service
./ethan webui     # écoute alors sur 3001
# retour production : sudo systemctl start ethan-runtime.service ethan-core.service
```

### Verdict final (mis à jour)

**PASS** — `http://localhost:3001` est le port officiel de la WebUI ETHAN et sert la
**dernière version** de l'interface (nav Open-WebUI v3, `/diagnostics`, nouveau design
system) via le chemin de production officiel (stack systemd + Docker). Le mode dev hôte
sur 3001 reste possible après arrêt sudo de la stack — commande documentée ci-dessus.
## Verdict final

**PASS** — ETHAN WebUI fonctionne réellement sur `http://localhost:3001`, sert la
nouvelle apparence (tokens + Inter), et la chaîne navigateur → 3001 → API :8000 est
opérationnelle.
---

## Annexe — Résolution du problème de login (mot de passe)

### Symptôme remonté par l'utilisateur
« Un problème avec le mot de passe du login » — impossible de se connecter à la WebUI.

### Diagnostic (causes successives, aucune liée au mot de passe lui-même)
1. `POST /auth/login` → **503 "Authentication service unavailable"** : le handler backend ne parvenait pas à interroger PostgreSQL.
2. Cause racine : **`relation "users" does not exist`** — la table `users` n'existait pas dans la base. Le schéma DB n'avait jamais reçu les migrations numérotées (`003` à `006`), non incluses dans `init.sql` monté au premier boot.

### Correction appliquée (procédure officielle du README des migrations)
```
docker exec -i ethan-postgres psql -U ethan -d ethan -v ON_ERROR_STOP=1 \
  < deploy/postgres/migrations/003_*.sql   # table users + admin par défaut (mdp 'admin')
docker exec -i ethan-postgres psql -U ethan -d ethan -v ON_ERROR_STOP=1 \
  < deploy/postgres/migrations/006_*.sql   # ALTER TABLE + seed (exit 0)
```

### Vérifications post-correction (via le port officiel :3001)
| Test | Résultat |
|---|---|
| `POST :3001/api/auth/login` admin/admin | ✅ **200** + JWT (144 car.) |
| Mauvais mot de passe | ✅ **401** (rejet correct) |
| `GET /api/v1/agents` avec Bearer | ✅ **200** |
| `GET /api/providers` avec Bearer | ✅ **200** |
| `GET /api/v1/settings` avec Bearer | ✅ **200** |

### Chaîne complète validée
```
Navigateur → localhost:3001 (WebUI) → /api/* (proxy) → ETHAN API :8000 → PostgreSQL ✅
```

### Identifiants par défaut (à changer en production)
- Utilisateur : `admin` / Mot de passe : `admin` (créé par la migration `003`)

### ⚠️ Recommandation infrastructure
Le problème se reproduira sur toute base recréée à neuf : envisager d'inclure l'application des migrations numérotées (`003`→`006`) dans `deploy/postgres/init.sql` ou dans l'entrypoint du conteneur `ethan-api` (à traiter côté infrastructure, hors périmètre UI).