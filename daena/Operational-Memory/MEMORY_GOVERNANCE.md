# ETHAN — Gouvernance de la mémoire technique

Date : 2026-11-03
Statut : PROPOSED
Nature : document normatif pour l'usage humain et agent

## 1. Principe fondamental

La mémoire technique n'est pas une autorité applicative.

Elle décrit, elle ne gouverne pas le code. L'autorité finale reste :

1. le dépôt Git et son code ;
2. les tests et observations effectuées ;
3. les décisions humaines explicitement validées.

Cette règle s'aligne sur le principe Human Root of Trust d'ETHAN.

## 2. Rôle des agents

Les agents peuvent :

- lire et rechercher ;
- proposer des modifications ;
- produire des diagnostics ;
- documenter avec provenance ;
- soumettre une vérification ;
- créer des rapports ou des synthèses comme propositions.

Les agents ne peuvent pas :

- transformer seuls une proposition en décision approuvée ;
- contourner les autorisations ETHAN ;
- réécrire l'historique ;
- supprimer des preuves ;
- publier des données ;
- marquer un composant comme `VERIFIED` sans source vérifiable ;
- marquer une proposition comme décision.

Toute sortie d'agent concernant un état technique doit indiquer un niveau de confiance et une source.

## 3. Rôle humain

Seul le humain approuve :

- les décisions architecturales ;
- les changements de priorité majeurs ;
- l'identité source canonique ;
- la résolution des conflits non prouvés ;
- le passage vers une mémoire publique ou une documentation externe.

Les humains sont également responsables des sauvetages asymétriques, des exceptions et des dérogations.

## 4. Provenance et preuve

Chaque fait durable doit répondre à ces questions :

1. Qu'est-ce que je sais ?
2. De quelle source ?
3. À quelle date est-il vérifié ?
4. Quel statut lui est donné ?
5. Quelle contradiction, s'il y en a, est connue ?

La provenance se situe par défaut au niveau document.

Un fait sans provenance doit être `UNKNOWN` ou `INFERRED` selon les cas, jamais `VERIFIED`.

### Niveaux de confiance

- `high` : preuve directe et répétable.
- `medium` : convergence de plusieurs indices, pas de certitude complète.
- `low` : hypothèse explicable mais non confirmée.

## 5. États proposés par catégorie

| Catégorie | Statuts applicables |
|---|---|
| Decision | `PROPOSED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `DEPRECATED`, `SUPERSEDED` |
| Proposition | `PROPOSED`, `UNDER_REVIEW`, `IMPLEMENTED`, `REJECTED`, `DEPRECATED` |
| Component | `PLANNED`, `IMPLEMENTED`, `VERIFIED`, `DEPRECATED`, `UNKNOWN` |
| Incident | `OPEN`, `INVESTIGATING`, `MITIGATED`, `RESOLVED`, `VERIFIED`, `FALSE_POSITIVE` |
| Repair | `PROPOSED`, `APPROVED`, `IMPLEMENTED`, `VERIFIED`, `FAILED`, `ABANDONED` |
| Verification | `PENDING`, `PASSED`, `FAILED`, `INCONCLUSIVE`, `OBSOLETE` |
| Test | `RECORDED`, `VERIFIED`, `STALE`, `INVALIDATED` |
| Dependency | `CLEAN`, `VULNERABLE`, `REMEDIATED`, `ACCEPTED_RISK`, `UNKNOWN` |
| TechnicalDebt | `IDENTIFIED`, `ACCEPTED`, `FIXED`, `VERIFIED`, `WAIVED` |
| Evidence | `COLLECTED`, `TRUSTED`, `DISPUTED`, `RETRACTED` |
| AgentReport | `PROVISIONAL`, `REVIEWED`, `VALIDATED`, `REJECTED`, `ABANDONED` |

## 6. Règles de promotion

- `PROVISIONAL` vers `REVIEWED` : relecture humaine ou automatique avec preuve.
- `REVIEWED` vers `VALIDATED` : décision explicite.
- `VERIFIED` uniquement avec source, date et reproduction, quand c'est possible.
- `APPROVED` uniquement après action humaine explicite.
- `DEPRECATED` et `SUPERSEDED` ne sont jamais supprimés, seulement marqués.
- Une promotion manquante doit rester invisible jusqu'à preuve.

## 7. Archives et immutabilité

- Les archives brutes ne sont jamais réécrites.
- Si une correction est nécessaire, on crée un nouvel événement ou un nouvel objet.
- Les index peuvent être enrichis, pas les preuves.

Cela protège la traçabilité du dépôt et des rapports d'agents.

## 8. Sécurité

- Aucun secret dans la mémoire partagée.
- Aucune URL signée privée.
- Aucun dump de base de données ou d'environnement.
- Les artifacts racine suspects sont hors de la mémoire jusqu'à clarification.
- Les sources `.env` et `.secrets` restent localisés dans leurs propres emplacements.

## 9. Conventions pour les agents

Avant une action technique, un agent doit :

1. lire Operational-Memory ;
2. vérifier les faits importants dans Git et le dépôt ;
3. rechercher dans Knowledge et Archives ;
4. citer ses sources et ses dates ;
5. ne pas traiter une proposition comme acquise ;
6. mettre à jour les index si une structure nouvelle est créée.

Un agent ne doit jamais :

- supprimer une archive ;
- falsifier un status ;
- masquer un conflit ;
- ignorer l'origine d'une information ;
- publier directement une documentation sans validation.

## 10. Rapport et audit

Chaque audit futur doit inclure :

- faits vérifiés ;
- hypothèses et leur preuve ;
- problèmes non résolus ;
- décisions demandées ;
- date et lieu opérationnel.

Les agents doivent conserver les rapports précédents comme preuve. Leur suppression volontaire n'est jamais une partie de la routine.

## 11. Coordination avec les ADR/ESR/ASR existants

Les décisions validées peuvent être intégrées aux documents officiels `docs/adr/` et `docs/architecture/adr/`.

Le modèle Obsidian propose des identifiants et des statuts. Il ne remplace pas les ADR. Il fournit le micro-système de gestion pour la mémoire technique locale et pour les futurs systèmes RAG.

## 12. Validation

Cette gouvernance est proposée et vérifiée conceptuellement. Aucun changement applicatif ETHAN n'a été effectué. Le code reste inchangé.

Les documents `ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md` et `MEMORY_DATA_MODEL.md` forment le contrôle logique de ce document.
