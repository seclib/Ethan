# Décisions — ETHAN

Ce fichier distingue les décisions validées, les propositions et les hypothèses. Une ancienne intention n'est pas une décision validée tant qu'elle n'est pas marquée comme telle avec une trace documentaire.

## Décisions validées

### D-001 — Hybride WebUI (2026-08-17)

- **Statut** : validée.
- **Source** : `Obsidian/Engineering/Audits/00-ETAT-DES-LIEUX.md`, section « Contradiction résolue — Décision validée (2026-08-17) ».
- **Contenu** : conserver la WebUI Next.js existante comme base, enrichir avec les concepts UX d'Open WebUI, ne pas abandonner la base existante.
- **Conséquence** : la stratégie de migration historique mentionnant un fork Open WebUI est adaptée, pas suivie littéralement.

### D-002 — Mémoire Codex minimale sans code applicatif (2026-11-01)

- **Statut** : validée au titre de la demande documentaire ; validation inter-sessions reste à confirmer.
- **Source** : requête utilisateur et ajout dans `docs/memory/`.
- **Contenu** : mettre en place un système documentaire minimal, sans modification de code, de migration ou de configuration de production.

## Propositions non validées

### P-001 — Plan Phase 3D sécurité (session actuelle, non versionnée)

- **Statut** : proposition, pas décision validée.
- **Source** : échange de la session actuelle (non versionné), à croiser avec le dépôt.
- **Contenu** : `session_version`, gate d'autorisation central, machine d'états bootstrap, durcissement WebSocket et API keys.
- **Remarque** : tant qu'aucune implémentation et aucune validation tests n'est réalisée, ces éléments restent des propositions.

## Hypothèses / dette technique

- `core/auth` et l'authentification API sont potentiellement sur plusieurs frontières (`core/auth/`, `interfaces/api/auth.py`, `interfaces/api/main.py`) ; la consolidation devra être validée par des tests.
- Le volume important de changements locaux non commités complique toute comparaison avec l'état documentaire.
- Les rapports de session peuvent signaler des intentions non implémentées ; toujours croiser avec le dépôt.

## Règles de validation

- Toute décision ajoutée ici doit contenir au minimum : date, statut, source, contenu, conséquence pratique.
- Ne pas convertir une hypothèse en décision validée.
- Ne jamais archiver de secret ou de donnée personnelle.
