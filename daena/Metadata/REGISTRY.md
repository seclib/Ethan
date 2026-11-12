# ETHAN — Registre de routage de la mémoire

Date : 2026-11-03
Statut : PROPOSED
Nature : document contractuel pour les agents

Ce registre associe chaque type d'information à sa destination, son schéma et sa gestion. Il complète `AGENTS.md`, `README.md`, `INDEX.md` et les schémas.

Présentation de la structure :

- `destination` : chemin principal sous Obsidian.
- `format` : Markdown, YAML ou Markdown + YAML.
- `schema` : schéma défini dans `MEMORY_DATA_MODEL.md`.
- `identifiant` : préfixe et séquence recommandée.
- `statuts autorisés` : subset du modèle.
- `preuves` : minimum à joindre.
- `relations obligatoires` : liens attendus.
- `notes` : règles de gouvernance.

## Enregistrements et routage

| Type d'information | Couche | Destination | Format | Schéma | ID | Statuts | Preuves minimales | Relations |
|---|---|---|---|---|---|---|---|---|
| Événement technique | Historical | `Archives/Events/EVT-YYYY-NNN-*.md` (créer si nécessaire) | Markdown + YAML | EngineeringEvent | `EVT` | RECORDED, VERIFIED, OBSOLETE | source ou commandes | `cmp:*`, EVT précédents |
| Modification de code | Historical + Verified State | `Operational-Memory/` ou note dédiée `Knowledge/Changes/` | Markdown + YAML | EngineeringEvent | `EVT` | RECORDED, VERIFIED | commit, fichier(s), test | `cmp:*`, decisionRefs |
| Décision technique | Knowledge / Historical | `Knowledge/Decisions/DEC-YYYY-NNN-*.md` | Markdown + YAML | Decision | `DEC` | PROPOSED ... SUPERSEDED | source humaine, composants | `cmp:*`, evidence |
| Audit | Knowledge | `_meta/AUDIT-*.md` existant | Markdown | AgentReport | `RPT` | PROVISIONAL, REVIEWED | méthode, dates, chemins | evt, cmp |
| Incident | Knowledge / Operational | `Operational-Memory/BLOCKERS.md` et/ou `Knowledge/Incidents/` | Markdown + YAML | Incident | `INC` | OPEN ... FALSE_POSITIVE | date, logs résumés, composant | `cmp:*`, `rep:*` |
| Réparation | Historical | `Archives/Events/` ou `Knowledge/Decisions/` | Markdown + YAML | Repair | `REP` | PROPOSED ... ABANDONED | modification, test,rollback | `inc:*` |
| Vérification | Verified State | Operational ou Knowledge | Markdown + YAML | Verification, TestResult | `VER`, `TST` | PENDING ... INVALIDATED | commande, resultat, date | `cmp:*`, `tst:*` |
| Test | Knowledge / Verified State | `Knowledge/Tests/` ou `Operational-Memory` | Markdown + YAML | TestResult | `TST` | RECORDED, VERIFIED | console de tests, date | `cmp:*`, `ver:*` |
| Dépendance | Knowledge | `Knowledge/...` | Markdown + YAML | Dependency | `DEP` | CLEAN ... UNKNOWN | fichier manifeste, date, risques | `cmp:*` |
| Connaissance technique | Knowledge | `Knowledge/{Architecture,Composants,Sécurité,...}/` | Markdown + YAML | Knowledge | `KNW` | PROVISIONAL ... VALIDATED | source, synthèse, scope | `cmp:*`, evt |
| Skill | Knowledge | `Knowledge/Skills/` (créer seulement si utilisation) | Markdown + YAML | Skill | `SKL` | PROVISIONAL, REVIEWED, VALIDATED | instructions, limites, tests | `cmp:*`, tools |
| Plugin et outil | Knowledge | `Knowledge/Tools/` (créer seulement si utilisation) | Markdown + YAML | Component | `CMP` | PLANNED ... UNKNOWN | API contract, santé, code | `dec:*` |
| Conversation | Archives | `Archives/Conversations/{agent}/` | Markdown | Archive brut | ID original | RECORDED | source native, date, agent | `ev:*` |
| Rapport d'agent | Archives | `Archives/Rapports-Agents/RPT-YYYY-NNN-*.md` | Markdown + YAML | AgentReport | `RPT` | PROVISIONAL ... ABANDONED | scope, findings, evidence | event/component |
| Preuve | Provenance | `_meta/` ou dossier adjacent | Markdown + YAML | Evidence | `EVD` | COLLECTED, TRUSTED, DISPUTED, RETRACTED | hash, lien, date | event/report |
| État opérationnel | Operational-Memory | `Operational-Memory/PROJECT_STATE.md` | Markdown | - | - | déclaratif daté | Git et résultats vérifiés | - |
| Proposition | Operational-Memory | `Operational-Memory/Proposals/` si nécessaire | Markdown + YAML | Proposition | `PROP` | PROPOSED, UNDER_REVIEW, IMPLEMENTED, REJECTED, DEPRECATED | source, statut | `cmp:*` |
| Dette technique | Operational-Memory | `Operational-Memory/BLOCKERS.md` ou `DEBT` dédié | Markdown + YAML | TechnicalDebt | `DEBT` | IDENTIFIED ... WAIVED | traces ou code | `cmp:*` |

## Règles de routage

- La tentation de créer un fichier par événement est forte. La préférer uniquement quand la taille justifie une archive.
- Si l'information est brève, l'ajouter à `PROJECT_STATE`, `TASKS` ou `BLOCKERS`.
- Si l'information est longue et réutilisable, créer un document structuré sous la bonne couche.
- Si la relation n'existe pas, signaler `UNKNOWN` au lieu d'improviser.
- Si une source ou preuve ne peut pas être citée, ne pas classer comme vérifié.

## Destination et nommage

Formats de nommage :
- Id-first pour les événements : `EVT-YYYY-NNN-agent-slug.md`
- synthèse : `KNW-YYYY-NNN-domaine-slug.md`
- decision : `DEC-YYYY-NNN-slug.md`
- incident : `INC-YYYY-NNN-slug.md`
- rapport agent : `RPT-YYYY-NNN-slug.md`

Les fichiers issus des anciens index restent en place jusqu'à validation humaine.

## Liens de référence

- Données : `_meta/FILE_MANIFEST.csv`
- Liens : `_meta/LINK_MANIFEST.csv`
- Architecture : `Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md`
- Modèle : `Knowledge/Architecture/MEMORY_DATA_MODEL.md`
- Gabarits : `Knowledge/Architecture/RECORD_TEMPLATES.md`
- Gouvernance : `Operational-Memory/MEMORY_GOVERNANCE.md`

## Validation automatique

Un agent doit pouvoir vérifier, par script :

- l'existence du fichier ;
- la présence d'un frontmatter YAML ;
- la présence des champs obligatoires ;
- la cohérence du statut selon la catégorie ;
- la résolution des relations ;
- la présence d'une source ;
- le calcul de l'empreinte si souhaité.

Conclusion : ce registre est la seule destination recommandée pour décider où enregistrer une information en mémoire. Les modifications de structure doivent être précédées d'une proposition.
