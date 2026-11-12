---
id: ECLL-001
title: ECLL — Overview
type: architecture
status: working
version: 1.0.0
tags:
  - ECLL
  - continuous-learning
  - experience-memory
---

# ECLL — Overview

## 1. But

Le **ETHAN Continuous Learning Loop (ECLL)** est un système documentaire et conceptuel permettant à ETHAN, à ses agents et aux futurs systèmes assistés par intelligence artificielle de capitaliser sur les expériences passées.

ECLL ne remplace pas :
- le code ;
- la mémoire runtime ;
- la recherche ;
- HROT.

Il fournit une mémoire d'expérience exploitable par des humains et des IA.

## 2. Principe fondamental

> ETHAN ne doit pas seulement savoir ce qu'il peut faire. Il doit savoir ce qu'il a déjà essayé, ce qui a fonctionné, ce qui a échoué, pourquoi, et dans quelles conditions une nouvelle tentative est justifiée.

## 3. Objectifs

- Retenir les tentatives réussies et échouées.
- Expliquer le contexte d'échec sans ambiguïté.
- Empêcher la répétition aveugle des approches.
- Justifier les nouvelles tentatives.
- Préserver l'immuabilité des événements historiques.
- Restituer une trajectoire technique compréhensible.

## 4. Relations avec ETHAN

ECLL est une couche documentaire et de capitalisation. Il s'appuie sur :

| Composant | Rôle |
|---|---|
| Obsidian | stockage durable et lecture humaine |
| Knowledge / Memory | recherche et mise en contexte |
| Reasoning | analyse et planification |
| Agents | exécution autorisée |
| Evaluation | vérification réelle |
| HROT | autorisation et contrôle |

## 5. Ce qui existe actuellement

- Les documents d'expérience existent dans `Obsidian/Engineering/Experiments`.
- Les sessions, décisions et projets sont documentés.
- ECLL documente désormais le cycle, les standards, les protocoles et les exemples.

## 6. Ce qui reste à implémenter

- L'indexation automatique du contenu.
- L'intégration en tant que comportement obligatoire des agents.
- Les tests automatisés de complétude documentaire.
- La mise en cohérence complète via le RAG si activé.

Voir aussi : [[ECLL-Architecture]], [[ECLL-Experience-Standard]], [[ECLL-AI-Operating-Protocol]], [[ECLL-Index]].
