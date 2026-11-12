# DECISIONS — ETHAN

## D-001 — Hybride WebUI (CONFIRMED)

- Date : 2026-08-17
- Statut : CONFIRMED
- Source : `Obsidian/Engineering/Audits/00-ETAT-DES-LIEUX.md`, section « Contradiction résolue — Décision validée (2026-08-17) »
- Contenu : conserver la WebUI Next.js existante comme base et l'enrichir avec les concepts UX d'Open WebUI.
- Conséquence : la stratégie historique de fork Open WebUI est adaptée, pas suivie littéralement.

## D-002 — Mémoire documentaire minimale (CONFIRMED pour le lot documentaire)

- Date : 2026-11-01
- Statut : CONFIRMED pour le lot documentaire ; validation inter-sessions à confirmer
- Source : requête utilisateur et ajout dans `docs/memory/`
- Contenu : mettre en place un système documentaire minimal sans modification code, migration ou configuration de production.
- Limites : cette décision concerne la mémoire, pas une implémentation applicative.

## D-003 — Mémoire consolidée Obsidian (IN_PROGRESS)

- Date : 2026-11-03
- Statut : IN_PROGRESS
- Source : migration documentaire contrôlée de cette session
- Contenu : créer `/home/fatsio/AI/Ethan/Obsidian` en conservant archives, connaissances et mémoire opérationnelle.
- Condition : les sources `ethan-knowledge` et `Odsidian` restent intactes.

## P-001 — Séparation Public/Private (PLANNED)

- Date : 2026-11-03
- Statut : PLANNED
- Source : `/tmp/ETHAN_PHASE2_SEPARATION_PLAN.md`
- Contenu : branche publique neuve par allowlist, historique privé préservé localement, contrôles secrets et licences.
- Limite : aucune implémentation réalisée.

## P-002 — Composition des versions divergentes (PLANNED)

- Date : 2026-11-03
- Statut : PLANNED
- Source : `/tmp/ETHAN_OBSIDIAN_MERGE_PLAN.md`
- Contenu : conserver les quatre versions divergentes et résoudre leur conflit par une version réconciliée documentée.
- Limites : aucune version réconciliée finale n'a encore été produite.

## D-003 — Report de la migration `transitFeeds.js` vers `odin/geo` (ODIN C3.5/C3.7)

- Date : 2026-11-09
- Statut : CONFIRMED (règle utilisateur explicite, audit C3.5 puis ré-confirmation audit cumulatif C3.7)
- Source : audits READ-ONLY C3.5 et C3.7, dépôt `/home/fatsio/AI/Ethan/examples/odin`
- Composants : `src/data/transitFeeds.js`, `scripts/package-boundaries.json` (groupes `transit-provider` node, `transit-source`, `transit-standalone`, `transit-layer`, `transit-service`, `tools`)
- Contenu : DEFERRED — la migration exigerait +3 modules (`src/geo/{index,crs,geometry}.js`) dans six groupes de boundary pour un wrapper exporté et un call site interne ; élargissement d'autorisations disproportionate au bénéfice d'une ligne d'import. Le symbole consommé est identique derrière la façade.
- Limites : décision réversible si un sous-chemin plus étroit que `./geo` est publié, ou si les groupes transit deviennent du premier ordre pour l'écosystème géo ; la migration ré-évaluée ne modifie pas le comportement.
- Relations : `Engineering/Plans/ODIN_C3_GEOSPATIAL_CAMPAIGN.md` §6 ; `Knowledge/Architecture/ODIN_GEOSPATIAL_API.md` §4.2

## H-001 — Surfaces d'authentification

- Statut : UNKNOWN / à valider par tests
- Source : `docs/memory/DECISIONS.md`
- Contenu : `core/auth`, `interfaces/api/auth.py` et `interfaces/api/main.py` sont potentiellement surplusieurs frontières.
- Action requise : consolidation validée par tests, non effectuée dans cette migration.

## Sources de vérité

Une intention ancienne n'est pas une décision validée. Seules les entrées marquées CONFIRMED peuvent être considérées comme fermes. Les entrées PLANNED et UNKNOWN ne justifient pas de modification applicative.
