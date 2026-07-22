# ETHAN - Runbook Opérationnel

Ce document décrit les procédures opérationnelles pour maintenir, dépanner et opérer la plateforme ETHAN.

## 1. Démarrage et Arrêt de la Plateforme

### Démarrage standard (Développement)
```bash
./ethan up
```
Cela démarre la stack de base : API, Kernel, Modules, NATS, Redis, Postgres.

### Démarrage avec Observabilité (Production/Debug)
```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d
```
Cela ajoute Grafana, Loki, Promtail, Vault et Jaeger à la stack de base.

### Arrêt de la plateforme
```bash
./ethan down
```
_Note: Les volumes (bases de données, logs, secrets) sont préservés._

## 2. Sauvegarde et Restauration

### Sauvegarde PostgreSQL
Un système de backup automatique est configuré via le service `pg-backup` (activé dans `docker-compose.cluster.yml`).
Pour déclencher un backup manuel immédiatement :
```bash
docker exec ethan-pg-backup kill -SIGUSR1 1
```
Les backups sont stockés dans le volume Docker `pg_backups`. Pour y accéder depuis l'hôte :
```bash
docker run --rm -v pg_backups:/var/backups/ethan -v $(pwd):/host alpine cp -r /var/backups/ethan /host/
```

### Restauration PostgreSQL
1. Assurez-vous que l'API et le Kernel sont arrêtés.
2. Copiez le fichier de backup dans le conteneur postgres :
```bash
docker cp ethan_20260720_080000.sql.gz ethan-postgres:/tmp/
```
3. Restaurez la base de données :
```bash
docker exec -it ethan-postgres bash -c "zcat /tmp/ethan_20260720_080000.sql.gz | psql -U ethan -d ethan"
```

## 3. Observabilité et Tracing

### Grafana (Dashboards)
- **URL** : http://localhost:3001
- **Identifiants** : admin / ethan-grafana (ou valeur de `GRAFANA_ADMIN_PASSWORD`)
- **Utilité** : Visualiser les métriques système, l'état de NATS et l'activité des modules cognitifs.

### Jaeger (OpenTelemetry)
- **URL** : http://localhost:16686
- **Utilité** : Tracing distribué. Permet de suivre le cycle de vie d'un événement depuis l'API Gateway jusqu'au traitement par les modules cognitifs.

### Loki & Promtail (Logs)
- **Accès** : Via l'interface Explore de Grafana.
- **Utilité** : Agréger les logs de tous les conteneurs Docker. Filtrer par `{compose_project="ethan"}`.

## 4. Gestion des Secrets (Vault)

- **URL** : http://localhost:8200
- **Token Dev** : `ethan-root-token` (ou valeur de `VAULT_DEV_ROOT_TOKEN_ID`)
- **Utilité** : Stockage sécurisé des clés d'API (OpenAI, Anthropic, etc.) et des mots de passe.

## 5. Dépannage Courant

### "Module not connecting to NATS"
1. Vérifiez l'état du cluster NATS :
   ```bash
   docker compose logs nats-1 nats-2 nats-3
   ```
2. Vérifiez la configuration réseau. Les modules doivent utiliser l'URL : `nats://nats-1:4222,nats-2:4223,nats-3:4224` (si le patch cluster est utilisé).

### "API Gateway returns 503"
L'API effectue un healthcheck sur ses dépendances (NATS, Redis, Postgres).
1. Vérifiez les logs de l'API :
   ```bash
   docker logs ethan-api
   ```
2. Consultez le point de terminaison détaillé : `http://localhost:8000/health/detailed`

### "High memory usage on Kernel"
1. Consultez Grafana pour identifier les fuites de mémoire.
2. Redémarrez le Kernel en douceur :
   ```bash
   docker restart ethan-kernel
   ```

## 6. Mises à jour de la plateforme

La pipeline CI/CD pousse automatiquement les nouvelles images sur GitHub Container Registry (GHCR) lors d'une release (`vX.Y.Z`).
Pour mettre à jour votre environnement :
```bash
docker compose pull
./ethan up
```
