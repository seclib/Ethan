# ETHAN Knowledge Base

## Objectif

Cette base de connaissance technique centralise les conversations, rapports, plans,
décisions d'architecture, résultats de tests et procédures produits pendant le
développement d'ETHAN.

## Structure

```
Odsidian/
├── README.md              # Ce fichier
├── INDEX.md               # Index général avec liens relatifs
├── 00-Inbox/              # Documents importés à classer
├── 01-Archives/           # Conversations originales par agent
│   ├── cline/
│   ├── codex/
│   └── copilot/
├── 02-ETHAN/
│   ├── Architecture/      # Architecture, composants, flux
│   ├── Decisions/         # Décisions d'architecture (ADR/ESR référencés)
│   └── Development/       # Plans, implémentations, rapports
├── 03-Procedures/         # Installation, configuration, maintenance
├── 04-Incidents-Solutions/# Erreurs, causes racines, corrections
├── 05-Tests-Validations/   # Tests exécutés et résultats
├── 06-Syntheses/          # Synthèses techniques (référencent les archives)
└── _meta/                 # Conventions, schémas, suivi des sources
```

## Règles

1. **Pas de vault Obsidian** : fichiers Markdown standard uniquement.
2. **Liens relatifs** : tous les liens internes sont relatifs.
3. **Archives immuables** : les conversations archivées ne sont jamais modifiées.
4. **Synthèses séparées** : les synthèses référencent leurs sources.
5. **Pas de secrets** : aucun token, clé API ou mot de passe n'est archivé.
6. **Provenance** : chaque archive indique sa source originale.

## Collecte

La collecte est effectuée par le module `core/knowledge/agent_traces/` :

```bash
python scripts/ethan-knowledge-sync.py --root ~/AI/Ethan/Odsidian
```

## Conventions de nommage

Format : `YYYY-MM-DD_agent_projet_sujet.md`

Exemple : `2026-10-28_cline_ethan_docker-fix.md`
