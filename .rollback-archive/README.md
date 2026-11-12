# Archive de rollback — Intégration « Tool Applications » abandonnée

Généré le 2026-10-03 lors de l'audit final du rollback ETHAN.

## Contexte

Le système de lancement d'applications externes (Osiris-Lab, NOMAD/MONAD,
OpenCTI, Agentic-Bug-Hunter) a été retiré du dépôt : routeur API, registre /
gestionnaire de déploiement, surface WebUI « Applications », manifests,
variables d'environnement, câblage socket Docker, tests et ADR associés.

Ces fichiers **n'ont jamais été commités** (non suivis par Git). Ils ne sont
donc pas récupérables via `HEAD` ni via les checkpoints Cline.

## Source

Extraits de l'image Docker dangling `ab35f5a6faee` (dernière image de l'API
construite **avant** le rollback). Contenu vérifié identique à l'image
`ethan-api:tool-manager-check`.

## Contenu

```
src.tgz   (103 Ko, 43 fichiers)
├── core/deployment/                    (registre, gestionnaire, docker/, xfce/)
└── interfaces/api/routers/tool_applications.py
```

## Restauration

```bash
tar xzf src.tgz -C /home/fatsio/AI/Ethan
```

Puis re-brancher dans `interfaces/api/main.py` (`include_router`) et rebuild :
```bash
docker compose build api && docker compose up -d api
```

## Note

Ce dossier est exclu via `.git/info/exclude` (local, non versionné).
Il peut être supprimé une fois le rollback définitivement acté.