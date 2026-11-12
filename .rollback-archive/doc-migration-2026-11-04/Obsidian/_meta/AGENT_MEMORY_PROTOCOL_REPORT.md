# AGENT_MEMORY_PROTOCOL_REPORT — ETHAN

Date : 2026-11-03

## 1. Objectif

Durcir le protocole d'utilisation de la mémoire pour les agents et documenter où enregistrer chaque type d'information, quels schémas utiliser et comment conserver l'historique.

## 2. Fichiers contrôlés

- `AGENTS.md`
- `INDEX.md`
- `Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md`
- `Knowledge/Architecture/MEMORY_DATA_MODEL.md`
- `Knowledge/Architecture/RECORD_TEMPLATES.md`
- `Operational-Memory/MEMORY_GOVERNANCE.md`
- `Metadata/REGISTRY.md`

## 3. Fichiers créés ou modifiés

Créés :

- `Knowledge/Architecture/RECORD_TEMPLATES.md`
- `Metadata/REGISTRY.md`
- `_meta/AGENT_MEMORY_PROTOCOL_REPORT.md`

Modifiés :

- `AGENTS.md`
- `INDEX.md`

## 4. Contrôles effectués

- Lecture intégrale des documents concernés.
- Validation UTF-8.
- Recherche de caractères de contrôle ou de zéro-width.
- Vérification des liens directs dans les documents modifiés et ajoutés.
- Vérification que chaque catégorie du registre possède une destination, un schéma et une règle de statut.
- Vérification que les templates couvrent au moins les objets suivants : `EngineeringEvent`, `Decision`, `Component`, `Verification`, `Incident`, `Repair`, `Knowledge`, `Skill` et `Evidence`.
- Vérification que les instructions ne confondent pas proposition, décision et vérification.
- Scan Gitleaks sur `Obsidian` : `no leaks found`.
- Vérification qu'aucun code applicatif ETHAN n'a été modifié.
- Vérification que `/home/fatsio/AI/Ethan-Public-Candidate` n'a pas été touché.

## 5. Contrôles réussis

- `AGENTS.md` est un point d'entrée obligatoire, court, avec références explicites.
- Les types d'enregistrements ont une destination, un schéma et une gestion de statuts.
- Les statuts sont distincts selon la catégorie.
- Les relations et les preuves minimales sont prescrites.
- Les agents peuvent déterminer où enregistrer une information avec `REGISTRY.md`.
- Les documents propres ont 0 lien cassé.
- Le dépôt Git principal et la mémoire n'ont pas dérivé au-delà des fichiers prévus.
- Les sources originales et archives restent intactes.

## 6. Points opératoires

- Le registre utilise des destinations proposées comme `Knowledge/Skills/`, `Knowledge/Tools/`, `Archives/Events/`, qui doivent être créées seulement lorsqu'un premier enregistrement réel en a besoin.
- Le registre est compatible avec une lecture humaine, textuelle, scriptée, un futur RAG et un graphe de connaissances.
- Les agents ne peuvent pas promouvoir une proposition en décision approuvée.
- Les agents ne peuvent pas transformer une implémentation en preuve sans vérification.

## 7. Problèmes restant à résoudre

- La correspondance définitive entre l'ancien arborescence Source B et la destination proposée reste à arbitrer.
- Certains types de validation applicative manquent de preuves directes récentes.
- Le registre n'a pas été validé par un automate externe.
- La navigation publique n'est pas concernée.

## 8. Décision

`PHASE_2_PROTOCOL_COMPLETE_WITH_WARNINGS`

Le protocole, le registre et les gabarits sont exploitables. Les points restant sont des arbitrages documentaires, pas des contradictions bloquantes. Aucune implementation applicative n'a été effectuée.


## 9. Mise à jour Phase 3

- `Obsidian/Metadata/REGISTRY.md` a été créé comme registre demandé.
- `Obsidian/_meta/REGISTRY.md` a été conservé comme pointeur, sans duplication complète.
- Les références centrales ont été mises à jour de `_meta/REGISTRY.md` vers `Metadata/REGISTRY.md`.
- `Knowledge/Architecture/RECORD_TEMPLATES.md` fournit les gabarits documentaires pour les opérations.
- Les liens propres vérifiés après modification sont à 0 cassé.
