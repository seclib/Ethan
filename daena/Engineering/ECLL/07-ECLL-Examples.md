---
id: ECLL-007
title: ECLL — Examples
type: examples
status: working
version: 1.0.0
tags:
  - examples
---

# ECLL — Examples

## 1. Tentative réussie

Exemple : normalisation du tag `ethan-api:latest`.

- Hypothèse : pointer le tag vers l'image active corrige l'incohérence de déploiement.
- Vérification : comparaison de l'Image ID taggé avec l'Image ID du conteneur, plus `/health`.
- Résultat : WORKING.
- Leçon : un tag ne définit pas une image; la vérité est son Image ID.

## 2. Tentative échouée puis nouvelle approche

Exemple : intégration ComfyUI dans Tools.

- Première situation : API live sans routes application-integration et stockage source absent dans le conteneur.
- Tentative précédente : suppression et reconstruction d'images.
- Échec partiel : interface n'affiche pas ComfyUI tant que source et stockage absents dans le conteneur.
- Nouvelle approche : montage en lecture du dépôt source et du stockage SQLite, reconstruction contrôlée.
- Résultat : WORKING après correction des causes racines (routes, source, stockage).

## 3. Tentative partiellement validée

Exemple : état runtime ComfyUI.

- Objectif : représenter `installed`, `running`, `healthy`.
- Résultat actuel : ComfyUI est `validated` et visible dans le catalog.
- Reste : l'état runtime réel n'est pas encore observé activement.
- Statut : PARTIAL.
