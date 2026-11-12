# Capacites optionnelles — validation Settings -> Capabilities

Date : 2026-11-04

## Etat observe

- langchain : READY (environnement isole detecte)
- chromadb : READY (environnement isole detecte)
- langgraph : READY (environnement isole detecte)
- qdrant : NOT_INSTALLED (aucun conteneur declare actif)

## Validation navigateur

Non effectuee : aucun navigateur Playwright / Chromium disponible.

## Constat API

- liste des composants accessible via `/v1/components`
- detect disponible et reflechit les etats reels
- les actions install/start/enable/logs existent et passent par le Core

## Limites

- pas de HROT runtime demonstre
- pas de changement de dependances Core global
- pas de verification visuelle

## Conclusion

La detection multi-environment est operationnelle.
Le reste du cycle via Settings reste PARTIELLEMENT_VALIDATED.
