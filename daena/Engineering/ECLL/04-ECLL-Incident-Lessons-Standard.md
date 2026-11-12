---
id: ECLL-004
title: ECLL — Incident & Lessons Standard
type: standard
status: working
version: 1.0.0
tags:
  - incident
  - lesson
---

# ECLL — Incident & Lessons Standard

## 1. Trois documents

### Experience
Dé décrit une tentative particulière.

### Incident
Décrit un problème observé, son impact et sa résolution.

### Lesson / Knowledge
Décrit une connaissance réutilisable.

## 2. Relations

Les documents peuvent se référencer mutuellement sans dupliquer l'ensemble du contenu.

Exemple :
- Expérience : tentative de déploiement d'une nouvelle image API.
- Incident : le conteneur actif utilisait une ancienne image.
- Leçon : vérifier l'Image ID réellement utilisé par le conteneur, pas seulement le tag local.

## 3. Format minimal

- Identifiant stable.
- Type de document.
- Relation vers les expériences associées.
- Cause ou hypothèse d'erreur.
- Mesures de prévention.
- Références de preuves.
