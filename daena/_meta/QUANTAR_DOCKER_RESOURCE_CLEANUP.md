# QUANTAR — Audit des ressources Docker post-validation

Date : 2026-11-04
Statut : audit exclusif, aucune modification ni suppression

## 1. Ressources observées

- Conteneur : `quantar-task` Exited (1)
- Image : `quantar-runtime:latest` (`dc8f2c77c463`)
- Volume ancien : `quantar_quantar_data` (com.docker.compose.project=quantar, hash legacy)
- Volume actuel : `quantar_quantar_task_data` (com.docker.compose.project=quantar, hash runtime)
- Réseau : `quantar_ethan_quantar_isolated`

## 2. Classification proposée

- `quantar_quantar_task_data` : `KEEP`
- `quantar_ethan_quantar_isolated` : `KEEP`
- `quantar_quantar_data` : `INVESTIGATE`
- `quantar-task` (Exited) : `BACKUP_THEN_REMOVE`
- `quantar-runtime:latest` : `KEEP`

## 3. Inspection

Aucune lecture du volume ancien n'a été effectuée sans accès.

Le rapport recommande une exportation read-only pour confirmation.

## 4. Plan (sans exécution)

1. Vérifier qu'aucun conteneur monte le volume ancien.
2. Exporter le volume ancien en mode read-only.
3. Comparer avec `quantar_quantar_task_data`.
4. Si aucune différence et documentation confirmée, supprimer uniquement `quantar_quantar_data`.
5. Documenter toutes les étapes.

## 5. Risques

- perte possible de données si volume ancien contenait des résultats ;
- confusion entre volume ancien et volume actuel ;
- suppression d'une image ou d'un conteneur encore utile par erreur.

## Conclusion

Aucune suppression effectuée. Le nettoyage reste conditionné à une inspection supplémentaire et à une validation humaine. Statut : `PARTIALLY_VALIDATED`.
