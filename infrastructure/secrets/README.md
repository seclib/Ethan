# Secrets ETHAN

**ATTENTION** : Ne jamais commiter les fichiers `.txt` contenant les secrets en clair.

## Structure

```
infrastructure/secrets/
├── README.md               ← Ce fichier
├── postgres_password.txt   ← Mot de passe PostgreSQL (AJOUTER DANS .gitignore)
├── api_key_openai.txt      ← Clé API OpenAI (AJOUTER DANS .gitignore)
└── api_key_anthropic.txt   ← Clé API Anthropic (AJOUTER DANS .gitignore)
```

## Procédure d'utilisation (Docker secrets)

1. Créer les fichiers de secrets locaux :
```bash
echo "mon_mot_de_passe_securise" > infrastructure/secrets/postgres_password.txt
```

2. S'assurer que `.gitignore` contient :
```
infrastructure/secrets/*.txt
```

3. Docker Compose lit automatiquement les secrets définis dans la section `secrets:`.

## Migration future vers Vault

1. Ajouter le service `vault` dans `docker-compose.yml`
2. Configurer `core/config/secrets.py` pour lire depuis Vault
3. Supprimer les Docker secrets

## Audit des secrets

Pour vérifier qu'aucun secret n'est commité :
```bash
trufflehog filesystem . --results=verified,unknown