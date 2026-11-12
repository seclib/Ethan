# INCIDENT RUNTIME-001 : NATS ne démarre pas

**Date** : 2026-07-21  
**Sévérité** : P0 - CRITIQUE  
**Status** : À corriger

---

## 1. Problème

```bash
$ sudo ethan up
...
4/4 — Healthchecks
  0s — 0/7 healthy, 0/7 running
  3s — 0/7 healthy, 0/7 running  
  ...
  TIMEOUT — Les healthchecks n'arrivent pas à un état healthy
```

## 2. Cause racine

```yaml
# docker-compose.yml - LIGNE 14
healthcheck:
  test: ["CMD-SHELL", "wget -qO- http://localhost:8222/healthz && nc -z localhost 4222 || exit 1"]
```

**Problème** : `nc -z` n'est pas disponible dans `nats:2.10-alpine` par défaut, ou wget échoue.

## 3. Symptômes

- NATS reste en `starting` indéfiniment
- Les services dépendants (API, kernel, modules) ne démarrent pas
- `./ethan status` montre `0/7 healthy`

## 4. Diagnostic

```bash
# Vérifier le conteneur NATS
docker compose ps nats
docker compose logs nats

# Tester le healthcheck manuellement
docker exec ethan-nats wget -qO- http://localhost:8222/healthz
docker exec ethan-nats nc -z localhost 4222 || echo "nc not found"
```

## 5. Correction (3 options)

### Option A : Corriger le healthcheck (RECOMMANDÉ)

```yaml
# docker-compose.yml - Remplacer le healthcheck NATS
healthcheck:
  test: ["CMD-SHELL", "wget -qO- http://localhost:8222/healthz || exit 1"]
  interval: 5s
  timeout: 3s
  retries: 5
```

### Option B : Utiliser un script plus robuste

```yaml
# docker-compose.yml - Healthcheck NATS amélioré
healthcheck:
  test: ["CMD-SHELL", "curl -sf http://localhost:8222/healthz || wget -qO- http://localhost:8222/healthz"]
  interval: 5s
  timeout: 3s
  retries: 10
```

### Option C : Ajouter netcat au conteneur

```yaml
# Créer deploy/Dockerfile.nats
FROM nats:2.10-alpine
RUN apk add --no-cache curl netcat-openbsd
```

## 6. Test de correction

```bash
# 1. Arrêter les services
./ethan down

# 2. Appliquer le patch
# Modifier docker-compose.yml

# 3. Redémarrer
./ethan up

# 4. Vérifier
./ethan status
# Doit montrer : NATS : healthcheck OK
```

## 7. Impact

- **Avant** : NATS ne passe jamais en `healthy`, blocage du stack
- **Après** : NATS passe en `healthy`, les dépendances démarrent

## 8. Prévention

Ajouter dans `scripts/cmd-doctor.sh` :

```bash
# Section 6 : Vérifier NATS healthcheck
check_nats_health() {
    section "6. NATS Health"
    
    if docker ps --filter "name=ethan-nats" --format '{{.Status}}' | grep -q "healthy"; then
        check_pass "NATS : healthy"
    elif docker ps --filter "name=ethan-nats" --format '{{.Status}}' | grep -q "starting"; then
        check_warn "NATS : still starting (healthcheck may fail)"
        show_fix "Healthcheck NATS peut utiliser nc indisponible" \
            "docker exec ethan-nats wget -qO- http://localhost:8222/healthz" \
            "docker-compose.yml (healthcheck nats)" \
            "high"
    else
        check_fail "NATS : not running"
    fi
}
```

---

**Priorité** : P0 - Bloquant