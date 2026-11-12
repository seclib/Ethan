# CapabilityManager — Convergence étudiée vers Rust

Date : 2026-11-04
Statut : proposition architecturale uniquement, aucune modification effectuée

## 1. Rust actuellement disponible

Modules réels :
- `core/rust/ethan_health/src/main.rs` : outil de santé Rust autonome ;
- `core/bus/backends/rust_event_store/src/lib.rs` : stockage d'événements Rust.

Autres composants Python dépendent de services Core Python pour l'API, la persistance et HROT.

## 2. CapabilityManager actuel

`core/capability_manager` contient :
- `types.py` : modèles et validation ;
- `backends.py` : backends d'installation ;
- `manager.py` : états, detect, install, lifecycle ;
- `builtin.py` : catalogue déclaratif ;
- `health.py` : health checks.

## 3. Responsabilités à préserver

- validation structurale ;
- gestion d'état et transitions ;
- détection réelle ;
- executors par backend ;
- hooks health/endpoints ;
- permissions via HROT ;
- audit/traces ;
- persistance de définitions et d'état.

## 4. Compatibilité et stratégie

Ne pas remplacer d'un coup. Options :
1. Garder la façade Python ;
2. déplacer croissament des tâches `detect` / `health` / `_run` vers le binaire Rust ;
3. exposer un contrat JSON local entre Python et Rust ;
4. conserver HROT et les permissions dans Core Python.

## 5. risques

- double source de vérité ;
- incohérence des états ;
- absence d'un adapter CLI ;
- permissions HROT non transmises à un processus Rust indépendant ;
- tests et migration coûteuses.

## 6. Plan

1. Stabiliser le contrat CapabilitySpec comme JSON schéma ;
2. déplacer la validation-injection et la détection dans un binary Rust ou service ;
3. conserver la façade Python pour les tests et l'API ;
4. migrer backend Docker/Python indépendamment ;
5. ajouter tests de parité et de HROT.

## Conclusion

La convergence est possible, mais pas par réécriture directe. Le Runtime Python actuel reste la source de vérité jusqu'à preuve contraire.
