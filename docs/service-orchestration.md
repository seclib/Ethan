# Orchestration des Services ETHAN

## Problème résolu

Le launcher indiquait que les services étaient opérationnels, mais le WebUI ne pouvait pas contacter `localhost:8000`. Le backend n'était pas réellement prêt.

### Symptômes

```bash
$ ./ethan up
✓ 7/7 services en cours d'exécution

$ ./ethan status
✓ API Gateway : UP
✓ WebUI : UP

# Mais dans le navigateur :
# WebUI ne peut pas contacter l'API
# localhost:8000 injoignable
```

### Cause racine

1. `./ethan up` démarrait les containers mais n'attendait pas les healthchecks
2. Le script déclarait "UP" après seulement 2 secondes (`sleep 2`)
3. Les services FastAPI/Redis/PostgreSQL prennent 5-30 secondes pour être réellement opérationnels
4. `./ethan status` ne vérifiait que l'état des containers, pas la connectivité réelle

## Solution

### 1. Attente des healthchecks dans `cmd-up.sh`

Le script `./ethan up` attend maintenant que **tous les healthchecks Docker** soient `healthy` avant de déclarer le système opérationnel.

**Modifications :**

```bash
# Avant
sleep 2
RUNNING=$(docker_compose ps --services --filter "status=running" | wc -l)
success "$RUNNING/$TOTAL services en cours d'exécution"

# Après
info "Attente des healthchecks (cela peut prendre 30-60s)..."
MAX_WAIT=90
WAITED=0
SLEEP_INTERVAL=3

while [ "$WAITED" -lt "$MAX_WAIT" ]; do
    HEALTHY=$(docker_compose ps --services --filter "health=healthy" 2>/dev/null | wc -l)
    TOTAL=$(docker_compose ps --services 2>/dev/null | wc -l)
    
    if [ "$TOTAL" -gt 0 ] && [ "$HEALTHY" -eq "$TOTAL" ]; then
        success "Tous les healthchecks sont OK ($HEALTHY/$TOTAL)"
        break
    fi
    
    dim "  Progression : $HEALTHY/$TOTAL healthy (${WAITED}s/${MAX_WAIT}s)"
    sleep "$SLEEP_INTERVAL"
    WAITED=$((WAITED + SLEEP_INTERVAL))
done
```

**Comportement :**
- Attend jusqu'à 90 secondes
- Affiche la progression toutes les 3 secondes
- Ne déclare "UP" que si tous les healthchecks sont `healthy`
- Timeout avec avertissement si les services ne sont pas prêts

### 2. Vérification de la connectivité réelle dans `cmd-status.sh`

Le script `./ethan status` vérifie maintenant :

- ✅ Healthcheck Docker (status du container)
- ✅ Connectivité réseau (port TCP)
- ✅ Endpoints HTTP (réponse réelle)
- ✅ Services spécifiques (NATS PING, Redis PING, PostgreSQL connexion)

**Exemple de sortie :**

```bash
$ ./ethan status

◆ Healthchecks détaillés

  ✓ ethan-nats : healthy
  ✓ NATS : port 4222 répond
  
  ✓ ethan-redis : healthy
  ✓ Redis : PING répond
  
  ✓ ethan-postgres : healthy
  ✓ PostgreSQL : connexion OK
  
  ✓ ethan-api : healthy
  ✓ API Gateway : /health répond
  
  ✓ ethan-kernel : healthy
  ✓ Core Kernel : port 8080 répond (si configuré)
  
  ✓ ethan-modules : healthy
  ✓ Cognitive Modules : container en cours d'exécution
  
  ✓ ethan-ui : healthy
  ✓ WebUI : répond

◆ 7/7 services opérationnels (healthy)
```

### 3. Correction de l'endpoint `/health`

**Fichier : `docker-compose.yml`**

Correction du healthcheck de l'API Gateway :

```yaml
# Avant
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health"]

# Après
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

**Raison :** L'endpoint réel est `/health` (défini dans `interfaces/api/routers/message.py`), pas `/v1/health`.

### 4. Correction de `cmd-status.sh`

Le script interrogeait `/api/v1/health` et `/api/v1/version`. Corrigé vers `/health` et `/version` :

```bash
# Avant
if curl -sf "http://localhost:${port}/api/v1/health" >/dev/null 2>&1; then
    success "$label : /api/v1/health répond"

# Après
if curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; then
    success "$label : /health répond"
```

## Architecture du flux de démarrage

```
./ethan up
    │
    ├─ docker compose up -d
    │   │
    │   └─ Démarre tous les containers
    │
    ├─ Boucle d'attente (max 90s)
    │   │
    │   ├─ Vérifie health=healthy pour chaque service
    │   ├─ Affiche progression toutes les 3s
    │   │
    │   └─ Condition de sortie :
    │       ├─ SUCCESS : Tous healthy → continue
    │       ├─ TIMEOUT : 90s écoulées → avertissement
    │       └─ ERREUR : Aucun service running → erreur
    │
    └─ Résumé final
        ├─ X/Y services opérationnels → SUCCESS
        ├─ X/Y services démarrés, Z/Y healthy → WARNING
        └─ X/Y services en cours → ERREUR
```

## Tests de connectivité

### NATS (port 4222)
```bash
nc -z localhost 4222
# ou
echo > /dev/tcp/localhost/4222
```

### Redis (port 6379)
```bash
redis-cli ping
# Réponse attendue : PONG
```

### PostgreSQL (port 5432)
```bash
PGPASSWORD=ethan_dev_pass psql -h localhost -U ethan -d ethan -c "SELECT 1"
```

### API Gateway (port 8000)
```bash
curl -f http://localhost:8000/health
# ou
curl -f http://localhost:8000/version
```

### WebUI (port 3000)
```bash
curl -f http://localhost:3000/
```

## Healthchecks Docker

Chaque service définit un healthcheck dans `docker-compose.yml` :

| Service | Healthcheck | Intervalle | Timeout | Retries |
|---------|-------------|------------|---------|---------|
| NATS | `nc -z localhost 4222` | 5s | 3s | 5 |
| Redis | `redis-cli ping` | 5s | 3s | 5 |
| PostgreSQL | `pg_isready -U ethan` | 5s | 3s | 5 |
| API Gateway | `curl -f http://localhost:8000/health` | 10s | 3s | 3 |
| Core Kernel | `curl -f http://localhost:8080/health` | 10s | 3s | 3 |

## Séquence de démarrage

Docker Compose garantit l'ordre grâce à `depends_on` + `condition: service_healthy` :

```yaml
api:
  depends_on:
    nats:
      condition: service_healthy
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy

ui:
  depends_on:
    api:
      condition: service_healthy
```

Flux :
1. NATS → healthy
2. Redis → healthy
3. PostgreSQL → healthy
4. API Gateway → démarre + healthcheck
5. Core Kernel → démarre + healthcheck
6. Cognitive Modules → démarre
7. WebUI → démarre (après API healthy)

## Vérification manuelle

### Tester que l'API répond

```bash
# Health endpoint
curl -f http://localhost:8000/health

# Version
curl -f http://localhost:8000/version

# Swagger
curl -f http://localhost:8000/docs
```

### Tester que la WebUI peut contacter l'API

```bash
# Depuis la WebUI (container ethan-ui)
docker exec ethan-ui curl -f http://api:8000/health

# Depuis localhost
curl -f http://localhost:8000/health
```

### Vérifier les healthchecks Docker

```bash
# Lister les services healthy
docker compose ps --services --filter "health=healthy"

# Détail d'un service
docker inspect ethan-api --format '{{.State.Health.Status}}'

# Logs du healthcheck
docker inspect ethan-api --format '{{.State.Health.Log}}'
```

## Timeout et diagnostics

### Timeout atteint

Si `./ethan up` atteint 90s :

```bash
⚠ Timeout atteint. Certains services peuvent ne pas être prêts.
```

**Actions :**

```bash
# Vérifier les services qui ne sont pas healthy
./ethan status

# Voir les logs d'un service
./ethan logs api
./ethan logs kernel

# Redémarrer un service spécifique
./ethan restart api
```

### Service en échec

Si un healthcheck échoue :

```bash
# Identifier le service
./ethan status | grep unhealthy

# Voir les logs
docker logs ethan-api --tail 100

# Redémarrer
./ethan restart api
```

## Fichiers modifiés

| Fichier | Modification | Raison |
|---------|--------------|--------|
| `scripts/cmd-up.sh` | Attente active des healthchecks | Garantir que les services sont prêts avant de déclarer "UP" |
| `scripts/cmd-status.sh` | Vérification de la connectivité réelle | Ne plus se baser uniquement sur `docker ps` |
| `docker-compose.yml` | Correction endpoint `/health` | Le healthcheck utilisait le mauvais chemin |

## Bonnes pratiques

### Pour les développeurs

```bash
# Démarrer les services avec attente automatique
./ethan up

# Vérifier l'état réel
./ethan status

# Si quelque chose ne va pas
./ethan logs <service>
./ethan doctor
```

### Pour le CI/CD

```bash
# Démarrer
./ethan up

# Attendre que les services soient prêts (dans ./ethan up)

# Vérifier avec le doctor
./ethan doctor --json > doctor.json

# Si doctor.json contient des FAIL, échouer le pipeline
```

### Pour la production

```bash
# Démarrer avec monitoring
./ethan up

# Vérifier régulièrement
./ethan status

# En cas de problème
./ethan logs api
./ethan restart <service>
```

## FAQ

**Q : Pourquoi 90 secondes de timeout ?**

R : Le service le plus lent est PostgreSQL qui peut prendre 20-30s pour être prêt. Les services applicatifs (API, Kernel) prennent ensuite 10-20s. 90s laisse une marge de sécurité.

**Q : Pourquoi ne pas utiliser `docker compose up --wait` ?**

R : Cette option n'existe pas dans toutes les versions de Docker Compose. La boucle manuelle est plus portable et affiche la progression.

**Q : Que faire si un service ne devient jamais healthy ?**

R : 
1. Vérifier les logs : `./ethan logs <service>`
2. Vérifier la configuration : `docker compose config`
3. Vérifier les dépendances : NATS, Redis, PostgreSQL doivent être healthy d'abord
4. Redémarrer : `./ethan restart <service>`

**Q : Comment désactiver l'attente ?**

R : Pour le développement rapide, vous pouvez commenter la boucle d'attente dans `cmd-up.sh`, mais ce n'est pas recommandé. Cela peut causer des problèmes de connectivité.

**Q : Pourquoi vérifier la connectivité dans `cmd-status.sh` ?**

R : Un container peut être "running" mais le service à l'intérieur peut être planté ou en train de démarrer. Les healthchecks et tests de connectivité garantissent que le service est réellement opérationnel.

## Maintenance

### Ajouter un nouveau service

1. Ajouter le service dans `SERVICES_LIST` dans `cmd-status.sh`
2. Ajouter le healthcheck dans `docker-compose.yml`
3. Configurer `depends_on` avec `condition: service_healthy`

### Modifier le timeout

Dans `scripts/cmd-up.sh` :

```bash
MAX_WAIT=90  # Modifier cette valeur
SLEEP_INTERVAL=3  # Modifier l'intervalle de vérification
```

### Ajouter un test de connectivité

Dans `scripts/cmd-status.sh`, ajouter un cas dans la boucle :

```bash
elif [ "$port" = "XXXX" ]; then
    # Test spécifique
    if <test>; then
        success "$label : <message>"
    else
        error "$label : <message>"
    fi