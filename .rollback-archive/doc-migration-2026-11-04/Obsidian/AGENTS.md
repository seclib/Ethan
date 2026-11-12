# AGENTS.md — Règles spécifiques à Obsidian/

Ce fichier est le point d'entrée obligatoire de la mémoire technique ETHAN pour tout agent. Il complète l'AGENTS.md racine et n'y ajoute que des règles propres à Obsidian/.

## 1. Rôle de ce dossier

`/home/fatsio/AI/Ethan/Obsidian` contient :

- des archives historiques ;
- des connaissances synthétisées ;
- des modèles de mémoire et de gouvernance ;
- une mémoire opérationnelle.

Ce n'est pas le moteur ETHAN. Les capacités applicatives restent dans `core/`, `runtime/` et `services/`. Les Archives sont historiques : elles décrivent ce qui a été fait et discuté, pas l'état technique actuel.

## 2. Initialisation obligatoire

À chaque intervention significative, lire dans cet ordre :

1. `AGENTS.md`
2. `README.md`
3. `Operational-Memory/PROJECT_STATE.md`
4. `Operational-Memory/DECISIONS.md`
5. `Operational-Memory/TASKS.md`
6. `Operational-Memory/BLOCKERS.md`
7. `Operational-Memory/MEMORY_GOVERNANCE.md`
8. `Knowledge/Architecture/MEMORY_DATA_MODEL.md`
9. `Metadata/REGISTRY.md`
10. `INDEX.md`
11. `_meta/FILE_MANIFEST.csv`
12. `_meta/LINK_MANIFEST.csv`, uniquement si nécessaire

Avant de modifier quoi que ce soit, comparer avec le dépôt réel via Git.

## 3. Recherche du contexte existant

Toute nouvelle déclaration doit chercher dans cet ordre :

1. Operational-Memory pour l'état confirmé.
2. Knowledge/Architecture pour le modèle et les schémas.
3. Knowledge pour les documents techniques.
4. Archives pour l'historique brut.
5. Rapports `_meta` pour les preuves et le contexte de migration.

Ne pas réutiliser une synthèse d'agent comme vérification de code.

## 4. Classification de l'information

Choisir d'abord la nature exacte de l'information :

| Nature | Couche | Destination | Schéma |
|---|---|---|---|
| fait opérationnel actuel | Verified Current State | `Operational-Memory/` | `Component` ou `EngineeringEvent` |
| événement | Historical Record | `Archives/Events/` | `EngineeringEvent` |
| décision | Technical Knowledge + historique | `Knowledge/Decisions/` | `Decision` |
| incident | Historical + Known State | `Knowledge/Incidents/` ou `Operational-Memory/BLOCKERS.md` | `Incident` |
| réparation | Historical Record | `Archives/Events/` ou `Knowledge/Decisions/` | `Repair` |
| vérification | Verified Current State | `Operational-Memory/` ou `Knowledge/...` | `Verification`, `TestResult` |
| dépendance | Technical Knowledge | `Knowledge/...` | `Dependency` |
| dette | Verified Current State | `Operational-Memory/BLOCKERS.md` | `TechnicalDebt` |
| preuve | Historical Record | `_meta/` ou dossier connexe | `Evidence` |
| rapport agent | Archives | `Archives/Rapports-Agents/` | `AgentReport` |

Si la nature n'est pas établie, utiliser `UNKNOWN` et une valeur `PROVISIONAL`.

## 5. Règles d'enregistrement

Pour toute activité significative, conserver :

- auteur humain ou agent ;
- date et contexte ;
- objectif ;
- composants concernés ;
- fichiers modifiés ;
- décisions associées ;
- commandes et tests pertinents ;
- résultats observés ;
- preuves ;
- statut final ;
- références aux événements précédents.

Les opérations mineures peuvent être condensées sous forme d'un court enregistrement `OPERATIONAL_NOTE`.

### Statuts

Suivre les statuts de `Memory Governance` sans les confondre :

- proposition ≠ décision ;
- implémentation ≠ vérification ;
- correction ≠ preuve de résolution ;
- rapport agent ≠ preuve indépendante.

## 6. Schémas et références

Les modèles se trouvent dans `Knowledge/Architecture/MEMORY_DATA_MODEL.md`.

Ne jamais créer un schéma ad hoc sans documenter l'identifiant, le statut, la provenance, les relations et la confiance.

Les relations doivent référencer des IDs existants. L'absence de références doit être justifiée.

## 7. Gestion de Knowledge et Skills

### Knowledge

- Connaissances techniques.
- Recherches.
- Documentation.
- Architecture.
- Sécurité.
- Sources et provenance.

### Skills

- Catalogue.
- Identité et version.
- Objectif.
- Instructions.
- Prérequis.
- Outils.
- Permissions.
- Limites.
- Tests.
- Historique des modifications.
- Statut d'approbation.

Ne pas recopier automatiquement les fichiers opérationnels des Skills dans Obsidian. Utiliser des références vérifiables et des archives de versions.

## 8. Vérification avant clôture

Avant de considérer un travail terminé :

1. comparer le changement avec le dépôt ;
2. confirmer le statut final ;
3. conserver la provenance ;
4. vérifier les liens si la structure a changé ;
5. mettre à jour les index concernés ;
6. ne pas transformer une synthèse en preuve d'exécution.

## 9. Sécurité

- Ne jamais stocker secrets, tokens, mots de passe, clés privées, cookies ni URL signées.
- Redacter avant publication ou diffusion externe.
- Respecter Human Root of Trust.
- Ne jamais traiter un candidat ou une proposition comme approuvé.

## 10. Références et règles propres

1. Ne jamais considérer une synthèse d'agent comme preuve de l'état actuel du code.
2. Vérifier dans le dépôt réel tout changement ou fonctionnalité affirmé.
3. Ne jamais modifier une archive dans `Archives/`.
4. Créer une description explicite d'origine et de date pour toute nouvelle synthèse.
5. Conserver les versions divergentes lorsque la différence est significative.
6. Mettre à jour `INDEX.md` lors d'un changement structurel.
7. Mettre à jour le rapport de migration ou équivalent pour une migration future.
8. Ne jamais effectuer de remplacement global aveugle de `Odsidian`, `ethan-knowledge` ou `docs/memory`.
9. Ne jamais supprimer les sources originales dans une tâche documentaire.
10. Ne jamais déclarer un état vérifié sans preuve.

## 11. Sources directes

- `Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md`
- `Knowledge/Architecture/MEMORY_DATA_MODEL.md`
- `Operational-Memory/MEMORY_GOVERNANCE.md`
- `Knowledge/Architecture/RECORD_TEMPLATES.md`
- `Metadata/REGISTRY.md`
- `_meta/PHASE_2_VALIDATION_REPORT.md`

---

Registre central :
`Metadata/REGISTRY.md`
