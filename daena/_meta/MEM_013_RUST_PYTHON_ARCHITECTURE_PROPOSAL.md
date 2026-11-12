# MEM-013 — RUST/PYTHON ARCHITECTURE PROPOSAL

Date : 2026-11-03
Statut : PROPOSAL — non approuvé
Nature : préparation d'arbitrage humain

## 1. Contexte

Engineering Memory est aujourd'hui implémenté en Python sous `core/engineering_memory`.
Le dépôt contient aussi deux crates Rust :

- `core/rust/ethan_health`
- `core/bus/backends/rust_event_store`

Le Rust est actuellement auxiliaire. Le service de mémoire est Python-first. Le bus Rust est en mode shadow si nécessaire.

La nouvelle préférence utilisateur est que Rust devienne le socle principal, Python le complément pour les intégrations et services LLM/ML.

Cette préférence ne constitue pas une décision approuvée tant que la révision n'est pas validée.

## 2. Composants existants déjà en Python

- `core/engineering_memory/models.py`
- `core/engineering_memory/validators.py`
- `core/engineering_memory/registry.py`
- `core/engineering_memory/persistence.py`
- `core/engineering_memory/service.py`
- `core/engineering_memory/adapters.py`
- `core/engineering_memory/security.py`
- `interfaces/api/routers/engineering_memory.py`

## 3. Artefacts Rust disponibles

- `core/rust/ethan_health`
- `core/bus/backends/rust_event_store`

## 4. Répartition préliminaire proposée

### Rust core possible

- lecture et écriture atomique du fichier ;
- envelopes et schémas bit-à-bit ;
- validation JSON canonique ;
- calcul d'éventuelles hashes ;
- persistance par append-only et formats ;
- transport performant ;
- file watching ;
- indexation lexical bas-niveau ;
- traitement de charges lourdes lorsqu'il est justifié.

### Python conserve

- routes FastAPI ;
- adaptateurs métier ;
- intégrations UI et contrôleurs ;
- LLM et providers ;
- interfaces Python de scripts et CLI ;
- connecteurs tools/plugins ;
- tests et simulation.

### Frontière

- Langage Rust :
  - inviolable pour les types et schémas si nécessaire ;
  - durable pour le stockage.
- Python :
  - acceptable pour l'orchestration et les services.
- Les deux communiquent via IPC/FFI, contrats explicites ou service co-localisé.

## 5. Risques

- Duplication des règles métier entre deux langages.
- Complexité des bindings.
- Cohérence transactionnelle entre Python et Rust.
- Sérialisation incompatible si un schéma dérive.
- Maintenance de deux crates + tests.
- Coût et latence des appels interprocessus.
- Absence de gain si la charge reste modérée.
- Surface d'attaque supplémentaire.

## 6. Stratégie progressive

### Phase A — parité

- Définir le contrat commun Rust / Python.
- Évaluer le coût en cycles et la volumétrie réelle.
- Tester le hash, les frontmatters et les ids.
- Ne rien migrer.

### Phase B — shadow

- Exécuter le service rust en mode shadow sans impact.
- Comparer les résultats avec Python.
- Documenter les divergences.

### Phase C — basculement contrôlé

- Introduire un mode `rust-primary` optionnel.
- Mesurer, tester, vérifier.
- Conserver la rollback à l'aide de configuration ou feature flag.

### Phase D — nettoyage

- Retirer le fallback Python seulement après validation humaine.

## 7. Critères de validation

- Même contenu canonique généré par les deux implémentations.
- Performance démontrée, pas supposée.
- Pas de perte d'événement.
- Pas de changement silencieux de données.
- Tests automatisés opposables.
- Documentation des régressions.
- Fallback possible.
- Confidentialité préservée.

## 8. Composants futurs Rust-only potentiels

- audit ingestion ;
- index local déterministe ;
- queue des événements ;
- byte-level report verifier.
