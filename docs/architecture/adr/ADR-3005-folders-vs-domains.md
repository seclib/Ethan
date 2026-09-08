# ADR-3005 — Folders (arborescence) vs Domains (étiquettes transverses)

**Statut** : Proposition (brouillon)
**Date** : 2026-09-07
**Contexte** : Deux mécanismes coexistent dans le Core et le WebUI :

- `core/folders/FolderManager` → `/v1/folders` → page `/folders` : **arborescence libre** de
ressources (Knowledge, RAG, Skills…) avec déplacement et multi-membreship ;
- `core/domains/DomainManager` → `/v1/domains` → page `/domains` : **regroupements sémantiques**
transverses (OSINT, Recon, Code) — étiquettes fortes.

Ces deux concepts ne dupliquent aucune ressource (relations par ID). Le risque est la confusion
produit (même famille de termes).

**Décision** :

1. **Ne pas fusionner** : Folders = organisation hiérarchique de rangement ; Domains =
classification sémantique transverse (multi-étiquetage).
2. Microcopie WebUI explicite : « Dossiers (arborescence) » vs « Domaines (groupes transverses) »,
avec une aide dans le hub Knowledge.
3. Documenter la distinction dans le guide utilisateur et les tooltips.

**Conséquences** :

- Aucun changement de schéma ni d'API existante.
- Clarification UX seule.

**Alternatives écartées** :

- Fusionner folders/domains (changerait le modèle sémantique — non requis).
- Supprimer l'un des deux (perte de capacité).
