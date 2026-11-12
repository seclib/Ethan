# QUANTAR — Réconciliation des mécanismes d'exécution

Date : 2026-11-04
Statut : implémenté avec tests contrôlés — PARTIALLY_VALIDATED

## 1. Problème initialement identifié

- `docker compose up -d` tentait de démarrer `quantar-task` sans fournir `task.json`.
- Résultat réel : `task file not found: /data/quantar/task.json`.
- L'exécution par `run_task_in_container` utilisait déjà `docker run` au lieu de Compose.

## 2. Analyse

- `run_task_in_container` crée le workspace et `task.json`, puis lançait une commande `docker run`.
- Compose seul ne connaissait pas le workspace.
- Il existait donc deux chemins incohérents.

## 3. Correction appliquée

- La commande générée par `_docker_run_command()` utilise maintenant :
  - `docker compose -f examples/quantar/compose.yaml run --rm`
  - le volume du workspace par tâche ;
  - les variables de task file/résultat.
- Les protections Compose restent source de vérité.
- Les paramètres d'isolement (read-only, user, cap_drop, no-new-privileges, network interne) sont conservés par compose.yaml.
- Aucune analyse réelle n'est démarrée.
- Aucune reprise automatique.

## 4. Tests

Tests exécutés :
- tests Quantar phase 36, phase 45 et runtime real-task

Résultat : 21 passed.

## 5. Limites

- le conteneur Compose one-shot ne démarre correctement qu'avec un `task.json` valide et son workspace correspondant ;
- les faux reports de progression sont recommandés pour la WebUI ;
- persistance et annulation restent à valider en runtime réel sur une tâche.

## 6. Risques restants

- dépendance au Docker daemon ;
- discordance entre les états HTTP et Docker ;
- gestion simultaneous de deux tâches identiques peut encore entrer en conflit ;
- proxy HROT non connecté.

Statut : PARTIALLY_VALIDATED.
