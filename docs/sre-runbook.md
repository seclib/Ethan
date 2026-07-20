# Runbook SRE — ETHAN Cognitive OS

**Version** : 1.0  
**Date** : 2026-07-20  
**Responsable** : SRE Team  

---

## 1. Architecture de référence

```
7 services Docker sur un réseau bridge ethan-core
  ├── nats:2.10-alpine         (4222, 8222, 6222)
  ├── redis:7-alpine           (6379)
  ├── postgres:16-alpine       (5432)
  ├── api (FastAPI)            (8000)
  ├── kernel (Python)          (8080)
  ├── modules (Python)         (—)
  ├── prometheus               (9090)
  └── ui (Next.js)             (3000)
```

---

## 2. Démarrage

### 2.1 Première installation

```bash
# 1. Prérequis
sudo apt install docker.io docker-compose-v2 curl wget
sudo usermod -aG docker $USER
newgrp docker

# 2. Cloner et installer
git clone git@github.com:seclib/Ethan.git
cd Ethan
./ethan install

# 3. Démarrer
./ethan up              # démarre tout (5-15 min si sans cache)
./ethan status          # vérifier que 7/7 sont healthy
```

### 2.2 Démarrage normal

```bash
./ethan up
```

**Temps attendu** : ~50s (cache) / ~10 min (première fois)

### 2.3 Services spécifiques

```bash
./ethan up nats redis postgres    # seulement l'infrastructure
./ethan up api kernel             # seulement l'application
```

---

## 3. Arrêt

### 3.1 Arrêt complet

```bash
./ethan down
```

### 3.2 Arrêt d'un service spécifique

```bash
docker compose stop api
docker compose rm -f api
```

---

## 4. Diagnostic

### 4.1 Vérification rapide

```bash
./ethan status
./ethan doctor
```

### 4.2 Logs

```bash
./ethan logs api           # logs de l'API
./ethan logs kernel        # logs du kernel
docker compose logs -f     # tous les logs en temps réel
docker compose logs --tail=100 nats
```

### 4.3 Healthchecks détaillés

```bash
curl http://localhost:8000/v1/health          # healthcheck simple
curl http://localhost:8000/health/detailed    # vérifie NATS + Redis + PostgreSQL
curl http://localhost:9090/metrics            # métriques Prometheus
```

### 4.4 Inspection Docker

```bash
docker compose ps                    # statut de tous les services
docker compose ps --services        # liste des services
docker compose top                  # processus dans chaque conteneur
docker compose logs --tail=50 -f    # logs en temps réel
```

---

## 5. Pannes connues

### 5.1 Service en statut `unhealthy`

**Symptôme** : `./ethan status` montre un service rouge

**Causes possibles** :
1. Dépendance non prête (NATS, Redis, PostgreSQL)
2. Port occupé sur l'hôte
3. Ressources insuffisantes (OOM)

**Actions** :

```bash
# 1. Vérifier la cause
docker compose logs <service> --tail=50

# 2. Vérifier les dépendances
./ethan status

# 3. Redémarrer le service
docker compose restart <service>

# 4. Si persiste, redémarrer tout le stack
./ethan restart
```

### 5.2 Build Docker échoué

**Symptôme** : `./ethan up` bloque sur le build

**Causes** :
1. Docker Hub inaccessible
2. pip install échoue
3. npm install échoue

**Actions** :

```bash
# 1. Vérifier Docker Hub
curl -sf https://registry-1.docker.io/v2/

# 2. Pull manuel des images
docker pull python:3.12-slim
docker pull node:20-alpine

# 3. Build avec logs verbeux
docker compose build --no-cache api
```

### 5.3 NATS inaccessible

**Symptôme** : kernel crash au démarrage

**Cause** : NATS pas encore prêt, timeout réseau

**Actions** :

```bash
# 1. Vérifier NATS
docker compose logs nats
curl -sf http://localhost:8222/healthz

# 2. Redémarrer NATS
docker compose restart nats

# 3. Vérifier le réseau
docker network inspect ethan_ethan-core
```

### 5.4 PostgreSQL crashé

**Symptôme** : API ou kernel en `unhealthy`

**Cause** : Volume corrompu, espace disque insuffisant

**Actions** :

```bash
# 1. Vérifier l'espace disque
df -h

# 2. Vérifier PostgreSQL
docker compose logs postgres --tail=30

# 3. Restaurer depuis le dernier backup (si configuré)
./ethan down
docker volume rm ethan_postgres_data
# Restaurer le backup
docker compose up -d postgres
```

### 5.5 Port déjà utilisé

**Symptôme** : conteneur refuse de démarrer

**Cause** : Un autre service utilise le port 8000, 8080, 3000, etc.

**Actions** :

```bash
# Identifier le processus occupant le port
sudo lsof -i :8000
# ou
ss -tlnp | grep 8000

# Modifier le port dans docker-compose.yml ou .env
```

---

## 6. Maintenance

### 6.1 Mise à jour

```bash
# Mettre à jour le code
git pull

# Rebuilder et redémarrer
./ethan update

# Vérifier
./ethan status
```

### 6.2 Backup manuel PostgreSQL

```bash
docker exec ethan-postgres pg_dump -U ethan ethan > backup_$(date +%Y%m%d).sql
```

### 6.3 Backup automatique (à configurer)

Ajouter dans crontab :
```bash
0 3 * * * cd /opt/ethan && docker exec ethan-postgres pg_dump -U ethan ethan > /var/backups/ethan/backup_$(date +\%Y\%m\%d).sql && find /var/backups/ethan -type f -mtime +30 -delete
```

### 6.4 Nettoyage des logs Docker

```bash
docker system prune -f --volumes  # supprime les logs, images, conteneurs inutilisés
docker compose logs --tail=0      # vide les logs actuels
```

### 6.5 Mise à jour des images de base

```bash
docker pull nats:2.10-alpine
docker pull redis:7-alpine
docker pull postgres:16-alpine
docker compose build --no-cache
./ethan restart
```

---

## 7. Surveillance

### 7.1 Métriques disponibles

| Endpoint | Port | Contenu |
|----------|------|---------|
| `/metrics` | 8000 | Prometheus (API Gateway) |
| `/v1/health` | 8000 | Healthcheck simple |
| `/health/detailed` | 8000 | Healthcheck avec dépendances |
| NATS monitoring | 8222 | Métriques NATS JetStream |

### 7.2 Alertes recommandées

| Alerte | Seuil | Action |
|--------|-------|--------|
| Service unhealthy > 3 min | 3 min | Relancer le service |
| Espace disque < 20% | 20% | Nettoyer logs + backups |
| RAM > 80% | 80% | Vérifier OOM, augmenter limits |
| Build échoué | 1 échec | Vérifier Docker Hub + pip |

---

## 8. Procédure de reprise après sinistre

### 8.1 Perte totale

```bash
# 1. Restaurer Docker
sudo apt install docker.io docker-compose-v2

# 2. Restaurer le dépôt
git clone git@github.com:seclib/Ethan.git
cd Ethan

# 3. Restaurer .env
cp .env.example .env
# Éditer .env avec les secrets

# 4. Restaurer PostgreSQL
docker compose up -d postgres
# Attendre que postgres soit healthy
cat backup_recent.sql | docker exec -i ethan-postgres psql -U ethan ethan

# 5. Démarrer tout le stack
./ethan up
```

### 8.2 Perte partielle (disque)

```bash
# Nettoyer l'espace
docker system prune -a --volumes -f

# Re-puller les images
./ethan up --skip-preflight