# TASKS — ETHAN

## Priorité haute

| Task | Statut | Source | Notes |
|---|---|---|---|
| Valider l'accessibilité et la visibilité de `seclib/Ethan` via GitHub | BLOCKED | environnement sans réseau et token invalide | metadata locale uniquement |
| Reconcilier `INDEX.md` Source A avec index Source B | IN_PROGRESS | `_meta/INDEX_ODSIDIAN_SOURCE.md`, `_meta/odsidian-metadata/...` | comptes contradictoires à résoudre |
| Vérifier la candidate publique avant toute publication | PLANNED | `/home/fatsio/AI/Ethan-Public-Candidate` | runtime WebUI non testé |
| Préparer la stratégie public/private | PLANNED | `/tmp/ETHAN_PHASE2_SEPARATION_PLAN.md` | aucune branche publique créée |

## Organisation documentaire

| Task | Statut | Source | Notes |
|---|---|---|---|
| Fusionner les sources de mémoire | IN_PROGRESS | `/tmp/ETHAN_OBSIDIAN_MERGE_PLAN.md` | copie effectuée, validation en cours |
| Conserver les six éléments uniques | CONFIRMED | `_meta/SOURCE_INVENTORY.md` | copies présentes et à vérifier par SHA |
| Consolider les 84 doublons exacts | CONFIRMED | hash comparison | un seul exemplaire dans la cible |
| Maintenir archives immuables | CONFIRMED | conventions du vault | pas de modification des archives |
| Tester les liens internes | IN_PROGRESS | `INDEX.md`, méta | script manuel et inspection |
| Mettre à jour les références `Odsidian` | PLANNED | dépôt principal | uniquement si nom final confirmé |

## Vérification et sécurité

| Task | Statut | Source | Notes |
|---|---|---|---|
| Rechercher secrets dans `Obsidian/` | IN_PROGRESS | outils locaux | exécuter gitleaks ou équivalent |
| Valider sources intactes après migration | IN_PROGRESS | `git status` et parité SHA | en cours |
| Comparer manifeste de copies | IN_PROGRESS | `_meta/MIGRATION_REPORT.md` | à compléter |
| Réorganiser les artifacts volumineux | PLANNED | inventaire | pas de déplacement automatique |

## Documentation

| Task | Statut | Source | Notes |
|---|---|---|---|
| Lire `AGENTS.md` principal comme règle de base | CONFIRMED | `/home/fatsio/AI/Ethan/AGENTS.md` | aucune duplication inutile |
| Actualiser `PROJECT_STATE.md` | IN_PROGRESS | cette migration | état Git du 2026-11-03 |
| Actualiser `DECISIONS.md` | IN_PROGRESS | cette migration | statuts confirmés/plannifiés |
| Maintenir `_meta/MIGRATION_REPORT.md` | IN_PROGRESS | cette migration | preuves à compléter |
