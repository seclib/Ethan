# ETHAN — Secrets Management

## 🔴 IMPORTANT : Migration vers Docker Secrets

Les fichiers texte en clair dans ce dossier sont **obsolètes et non sécurisés**.

Ne JAMAIS stocker de secrets dans des fichiers texte. La méthode `echo "pass" > file.txt` est interdite.

## Méthodes recommandées

### 1. Docker Secrets (recommandé pour Docker Compose)

```yaml
# docker-compose.yml
secrets:
  postgres_password:
    file: ./infrastructure/secrets/postgres_password.txt  # ← À REMPLACER
```

### 2. HashiCorp Vault (production)

```bash
# Setup Vault
docker compose -f docker-compose.vault.yml up -d vault

# Écrire les secrets
vault kv put ethan/postgres password="$(openssl rand -base64 32)"
vault kv put ethan/redis password="$(openssl rand -base64 32)"
vault kv put ethan/jwt secret="$(openssl rand -base64 64)"
```

### 3. Environnement + .env (dev uniquement)

```bash
# .env (ajouté à .gitignore)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)
```

## Commandes utiles

```bash
# Générer un secret solide
openssl rand -base64 32

# Vérifier qu'aucun secret n'est commité
grep -r "POSTGRES_PASSWORD=change-me" .env.example && echo "⚠️  Default password found"

# Scanner le dépôt pour des secrets
pip install trufflehog
trufflehog filesystem .