# ETHAN — Architecture de la mémoire technique

Date d'établissement : 2026-11-03
Statut : PROPOSED
Auteur : architecture technique ETHAN
Source opposable : `AGENTS.md`, `/home/fatsio/AI/Ethan/docs/memory/DECISIONS.md`, `Obsidian/_meta/RECONCILIATION_REPORT.md`

Ce document définit le modèle cible de la mémoire technique d'ETHAN. Il ne modifie pas le code applicatif et ne crée pas de données opérationnelles supplémentaires.

## 1. Objectif

La mémoire technique d'ETHAN doit permettre à un humain ou à un agent de reconstruire, vérifier et faire évoluer le projet sans dépendre de la mémoire narrative d'un agent.

Elle remplit quatre fonctions :

1. conserver l'historique réellement produit pendant le développement ;
2. organiser les connaissances techniques vérifiées ;
3. décrire l'état actuel avec sa provenance ;
4. isoler les propositions, les hypothèses et les faits.

Cette mémoire n'est pas le code. Elle ne remplace ni les tests, ni Git, ni les documents d'architecture applicative.

## 2. Trois couches obligatoires

### 2.1 Couche 1 — Historical Record

Contenu :

- événements architecturaux ;
- modifications et migrations ;
- décisions et propositions associées ;
- incidents ;
- réparations ;
- dépréciations ;
- sources et preuves.

Cette couche est très proche de l'append-only : on n'écrase pas le passé. Une modification ultérieure crée un nouvel événement ou une nouvelle réparation, même si elle remet en cause une conclusion antérieure.

### 2.2 Couche 2 — Technical Knowledge

Contenu :

- architecture cible ;
- composants ;
- interfaces ;
- dépendances ;
- concepts techniques ;
- conventions ;
- documentation réutilisable ;
- synthèses validées.

Cette couche doit rester cohérente avec le dépôt et ne doit jamais être traitée comme preuve à elle seule de l'état d'exécution.

### 2.3 Couche 3 — Verified Current State

Contenu :

- état réel et vérifié des composants ;
- fonctionnalités disponibles ;
- tests exécutés et resultados ;
- état des dépendances ;
- vulnérabilités connues ;
- dette technique connue ;
- traces de vérification ;
- date et méthode de validation.

Cette couche est la seule qui peut affirmer avec confiance l'état technique actuel d'ETHAN, et elle doit être rafraîchie régulièrement.

## 3. Relations d'autorité

En cas de contradiction, l'ordre d'autorité est le suivant :

1. État vérifié de `core/`, `runtime/`, `services/` et résultats de tests.
2. Schémas et documentation ADR/ESR/ASR et preuves citées.
3. Couche 3 — Verified Current State.
4. Couche 2 — Technical Knowledge.
5. Couche 1 — Historical Record.
6. Synthèses d'agents.
7. Rapports historiques, sauf preuve vérifiable.

Une décision PROPOSED ne vaut pas une décision APPROVED.

Une implémentation code ne vaut pas une vérification système.

Une correction documentée ne devient `VERIFIED` que par capacité de reproduire une preuve.

## 4. Identifiants et arborescence

### 4.1 Éléments à identifier

Chaque entité importante doit posséder un identifiant stable.

- Composant : `CMP-YYYY-NNN`
- Décision : `DEC-YYYY-NNN`
- Événement technique : `EVT-YYYY-NNN`
- Incident : `INC-YYYY-NNN`
- Réparation : `REP-YYYY-NNN`
- Vérification : `VER-YYYY-NNN`
- Dépendance : `DEP-YYYY-NNN`
- Test : `TST-YYYY-NNN`
- Dette technique : `DEBT-YYYY-NNN`
- Évidence : `EVD-YYYY-NNN`
- Rapport agent : `RPT-YYYY-NNN`

L'identifiant est un point de référence, pas une justification. La provenance reste attachée à chaque entrée.

## 5. Source de vérité et provenance

L'origine de chaque information durable doit être indiquée.

Champs recommandés :

- `id`
- `type`
- `status`
- `created_at`
- `updated_at`
- `source_of_fact`
- `provenance_level` : `observed`, `derived`, `inferred`
- `parents`
- `related_components`
- `evidence_refs`
- `supersedes`
- `superseded_by`
- `notes`

Sources possibles :

- commit Git et diff ;
- fichier de source du dépôt ;
- test exécuté avec résultat conservé ;
- configuration réelle ;
- documentation interne ;
- rapport d'audit ;
- observation d'un opérateur humain ;
- synthèse d'agent, marquée comme provisoire si non confirmée.

## 6. Contrats entre couches

### 6.1 Historical -> Knowledge

Les entrées de la couche 1 d'ont pouvoir d'enrichir la couche 2 seulement si :

- la source est identifiable ;
- la conclusion est traçable ;
- une revision ultérieure ne la rend pas obsolete sans mise à jour.

### 6.2 Knowledge -> Verified Current State

La couche 2 peut induire une hypothèse, mais la couche 3 ne s'appuie qu'aux preuves. Une contradiction entre Knowledge et Verified Current State doit être explicite.

### 6.3 Verified State -> Knowledge

La couche 3 peut mettre à jour la couche 2 avec une date et une transaction documentée. L'update ne doit pas effacer la raison de la correction.

### 6.4 Relations avec Git et les releases

Git reste la source de vérité du code. Les mémoires Obsidian sont des annotations et des synthèses, pas des code sources ni un runtime. Les commits, tags et PR font partie de l'historique technique officiel du projet.

## 7. Anti-contradiction

Trois mécanismes réduisent les contradictions :

1. Statuts propres à chaque entité.
2. Relations explicites (`related_component`, `conflicts_with`, `depends_on`, `verified_by`).
3. Règle de pré février : la connaissance qui est remplacée reste visible dans la couche historique.

Une synthèse ancienne ne doit pas disparaître de l'archive, mais doit être désactivée dans la vue courante par un état `DEPRECATED` ou `SUPERSEDED`.

## 8. Sécurité et gouvernance

### 8.1 Human Root of Trust

Les agents peuvent :

- lire et rechercher dans la mémoire ;
- proposer des modifications ;
- produire des diagnostics ;
- soumettre des résultats ;
- documenter leur travail.

Ils ne peuvent pas :

- transformer seuls une proposition en décision approuvée ;
- contourner les autorisations ETHAN ;
- réécrire l'historique ;
- supprimer des preuves ;
- promouvoir une information hypothétique sans décision humaine.

### 8.2 Données sensibles

Aucun secret, token, mot de passe, clé privée, cookie, URL signée ni donnée personnelle sensible ne doit être stocké dans la mémoire partagée.

Les archives et captures peuvent contenir de telles traces ; il faut les redacter avant tout usage partagé.

### 8.3 Statuts candidats

Un dossier `candidates/` éventuel contient des informations non officielles. Ces informations :
- peuvent être lues ;
- ne sont pas une source de vérité ;
- peuvent être promues seulement après validation humaine et passibilité d'un audit ;

### 8.4 Hors périmètre explicite

- `/home/fatsio/AI/Ethan-Public-Candidate` ne doit pas être synchronisé, modifié ou nettoyé depuis cet effort.
- Aucune diffusion sur GitHub ne doit être faite sans allowlist, scan et validation humaine.

## 9. Gouvernance documentaire par agents

Un agent doit toujours, pour une information importante :

1. citer la source ;
2. indiquer le niveau de confiance ;
3. marquer la donnée `PROPOSED`, `VERIFIED` ou `UNKNOWN` ;
4. ne pas classer comme décision une simple proposition ;
5. ne pas classer comme vérifié un état jamais validé ;
6. conserver la provenance si le document est transformé.

## 10. Migration et compatibilité

Cette architecture doit être introduite progressivement et de façon non destructive sur les sources existantes.

Le système de mémoire doit rester lisible sans interface graphique. Les agents peuvent l'interroger avec des commandes simples et avec des futurs accès RAG.

Les anciens index, ADR et reports restent la source primaire de preuve. Les nouveaux schémas sont des modélisations, pas des remplacements immédiats.

## 11. Livrables de cette phase

Trois documents sont produits avec cette phase :

1. `Obsidian/Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md`
2. `Obsidian/Knowledge/Architecture/MEMORY_DATA_MODEL.md`
3. `Obsidian/Operational-Memory/MEMORY_GOVERNANCE.md`

`AGENTS.md` dans `Obsidian/` est complété pour rappeler les règles spécifiques.

## 12. Validation

À la fin de cette phase sont vérifiés :

- la présence des livrables attendus ;
- la cohérence entre les statuts ;
- les liens ajoutés dans `INDEX.md` ;
- le fait qu'aucun fichier source n'a été modifié ;
- le respect des contraintes de taille et de lecture ;
- l'absence de secrets dans les nouveaux documents.

## 13. Points nécessitant approbation

1. Choix final du schéma de préfixes d'ID avant d'insérer des données.
2. Choix final des transitions de statut pour chaque catégorie.
3. Décision de créer ou non un ADR officiel dans `docs/adr/` pour cet architecture.
4. Décision concernant l'index historique et la navigation.
5. Décision concernant la future relation entre Obsidian et un espace public.

La route d'implémentation applicative n'est pas engagée à ce stade.

---

Principal document :
`Obsidian/Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md` : architecture des trois couches, autorité, sécurité et compatibilité.
