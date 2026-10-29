# AUDIT-ARCHIVES — Base de connaissance ETHAN

## Date de l'audit
2026-10-28

## 1. Inventaire récursif

### Structure existante
```
Odsidian/
├── README.md
├── INDEX.md
├── 00-Inbox/
├── 01-Archives/ (cline: 83, codex: 2, copilot: 2 = 87 sessions)
├── 02-ETHAN/{Architecture, Decisions, Development}/
├── 03-Procedures/
├── 04-Incidents-Solutions/
├── 05-Tests-Validations/
├── 06-Syntheses/by-agent/ (3 fichiers)
└── _meta/ (conventions.md, sync-state.json)
```

### Fichiers totaux : 93 (87 archives + INDEX + README + conventions + sync-state + 3 synthèses)

### Tailles des archives
| Catégorie | Nombre | Taille min | Taille max | Taille moyenne |
|-----------|--------|-----------|-----------|---------------|
| Cline | 83 | ~1 KB | 8.7 MB | ~1.5 MB |
| Codex | 2 | 3.9 MB | 7.8 MB | 5.9 MB |
| Copilot | 2 | ~50 KB | ~100 KB | ~75 KB |

### Fichiers anormalement volumineux (> 5 MB)
- `01-Archives/cline/2026-08-13/1786588790163.md` — 8.7 MB
- `01-Archives/codex/2026-10-23/01a16865-...29c2.md` — 7.8 MB
- `01-Archives/cline/2026-06-26/1782299840579.md` — 4.0 MB
- `01-Archives/codex/2026-10-23/01a16882-...fd9.md` — 4.0 MB
- `01-Archives/cline/2026-08-03/1785676074904.md` — 3.4 MB

## 2. Couverture par période

| Mois | Cline | Codex | Copilot | Total |
|------|-------|-------|---------|-------|
| 2026-06 | 25 | 0 | 0 | 25 |
| 2026-07 | 18 | 0 | 0 | 18 |
| 2026-08 | 40 | 0 | 0 | 40 |
| 2026-09 | 0 | 0 | 0 | 0 |
| 2026-10 | 0 | 2 | 2 | 4 |

### Analyse de la lacune septembre 2026
- **Cause** : Les tâches Cline s'étendent du 12 juin au 19 août 2026 (timestamps 1781261826788 à 1787143354523).
- **Aucune tâche Cline** n'existe après le 19 août 2026.
- **Conclusion** : Il n'y a pas de conversations Cline en septembre ou octobre 2026. Cline n'a pas été utilisé pendant cette période (ou les données ont été supprimées).
- **Action** : Documenter cette lacune, ne pas inventer de données.

### Analyse de la lacune octobre 2026
- **Codex** : 2 sessions du 23 octobre 2026 (collectées avec succès).
- **Copilot** : 2 sessions (avril et mai 2026, pas octobre).
- **Cline** : 0 sessions en octobre.
- **Conclusion** : Seules les sessions Codex sont disponibles pour octobre 2026.

## 3. Sources disponibles et leurs limites

| Agent | Mécanisme | Période disponible | Limitation |
|-------|-----------|-------------------|------------|
| Cline | JSON files (ui_messages, api_history, metadata) | 2026-06-12 → 2026-08-19 | Aucune donnée après août 2026 |
| Codex | JSONL (response_item) | 2026-10-23 | Seulement 2 sessions |
| Copilot | JSONL (events) | 2026-04-24, 2026-05-25 | Seulement 2 sessions, anciennes |
| ChatGPT Ext. | Aucun accès local | N/A | Non collectable |

## 4. Fichiers volumineux

### Problème
Les fichiers Codex sont particulièrement volumineux car ils incluent :
- Les instructions système complètes (skills, permissions, etc.) répétées à chaque tour
- Les résultats d'outils (souvent > 100 KB par résultat)
- Les messages de raisonnement (reasoning) avec le thinking complet

### Stratégie de découpage proposée
1. **Conversations Codex** : découper par "tour" (user message + assistant response + tool calls)
2. **Conversations Cline** : déjà par session, mais les plus longues (> 5 MB) devraient être découpées par sujet
3. **Seuil** : Pas de limite arbitraire. Découper aux frontières naturelles (messages, sujets)

### Fichiers à découper (> 5 MB)
| Fichier | Taille | Stratégie |
|---------|--------|-----------|
| cline/2026-08-13/1786588790163.md | 8.7 MB | Découper par sujet si possible |
| codex/2026-10-23/01a16865-...29c2.md | 7.8 MB | Découper par tour de conversation |
| cline/2026-06-26/1782299840579.md | 4.0 MB | Conserver (sous le seuil) |
| codex/2026-10-23/01a16882-...fd9.md | 4.0 MB | Conserver (sous le seuil) |

## 5. Doublons et liens

- **Doublons** : 0 détecté (vérifié par checksum SHA-256)
- **Liens cassés** : Aucun détecté dans l'INDEX.md actuel
- **Références** : Tous les liens dans INDEX.md sont relatifs et valides

## 6. Plan de correction

### Phase A — Découpage des fichiers volumineux
1. Créer un script de découpage pour les fichiers Codex (> 5 MB)
2. Découper par frontière de message (tour user/assistant)
3. Créer des fichiers numérotés : `...-part-01.md`, `...-part-02.md`
4. Mettre à jour l'INDEX.md avec les liens vers les parties

### Phase B — Création de la structure cible
1. Créer `02-A-Verifier/` pour les affirmations non confirmées
2. Créer `03-Connaissances-Verifiees/` pour la documentation validée
3. Créer `04-Tests-et-Preuves/` pour les résultats de tests
4. Créer `05-Decisions/` pour les décisions d'architecture
5. Créer `99-Metadonnees/` pour les index et rapports

### Phase C — Documentation des lacunes
1. Créer un rapport de couverture par mois
2. Documenter les sources non prises en charge
3. Ne pas inventer de données pour septembre 2026

## 7. Mécanismes de collecte existants

- **Script** : `scripts/ethan-knowledge-sync.py`
- **Module** : `core/knowledge/agent_traces/`
- **Tests** : `tests/test_agent_traces.py` (20 tests)
- **Documentation** : `docs/user-guide/agent-traces.md`

### Commandes de relance
```bash
# Synchronisation complète
python scripts/ethan-knowledge-sync.py

# Synchronisation d'un agent spécifique
python scripts/ethan-knowledge-sync.py --agents cline

# Vérification de l'idempotence
python scripts/ethan-knowledge-sync.py  # doit donner 0 collectées, N doublons
```
