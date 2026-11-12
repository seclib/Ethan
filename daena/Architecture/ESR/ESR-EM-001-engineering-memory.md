# ESR-EM-001 — Exigences système de la mémoire technique

Date : 2026-11-03
Statut : PROPOSED

## 1. Portée

La mémoire technique d'ETHAN doit rester accessible aux humains, aux scripts et aux agents. Elle collecte des événements techniques, valide les formats et leur gouvernance, persiste dans Obsidian et dans la persistance canonique déjà présente, puis propose une interrogation par API et références stables.

Les sources cumulées sont `Obsidian`, `core`, `docs`, le Git et les ADR/ESR/ASR.

## 2. Objectifs vérifiables

1. Enregistrement complet des activités liées à ETHAN.
2. Provenance identifiable pour tout fait durable.
3. Événements observés opposables aux déclarations d'agents.
4. Réutilisation des schémas et types existants.
5. Gouvernance explicite avec statuts.
6. Aucune dépendance au visuel.
7. Politique d'archivage et de rétention exprimée.
8. Compatibilité avec `/home/fatsio/AI/Ethan/docs/memory`.
9. Absence de secret.
10. Mode offline possible.

## 3. Exigences fonctionnelles

### 3.1 Événements

- F-01 : tout événement technique doit pouvoir posséder un type, un horodatage, un auteur, une source, une criticité, un composant, une description et des provenance.
- F-02 : un événement peut patienter en attente de validation.
- F-03 : un événement issu du runtime doit être identifiable comme observé.
- F-04 : un événement d'agent doit être identifiable comme déclaration.
- F-05 : le service doit pouvoir lister et filtrer des événements par type, composant, statut, intervalle et auteur.

### 3.2 Validation

- F-06 : les événements doivent être validables par schéma.
- F-07 : les transitions de statut incohérentes doivent être rejetées.
- F-08 : les champs manquants et les références liées doivent être détectés.
- F-09 : les provenance manquantes doivent conduire à une erreur ou à un état `UNKNOWN`.

### 3.3 Persistance

- F-10 : la persistance atomique doit rester possible.
- F-11 : Obsidian doit rester un store documentaire canonique hors code runtime.
- F-12 : Git doit rester la source officielle de code et de release.
- F-13 : les modifications SQL relationnelles doivent être possibles sans remplacer les documents Markdown.
- F-14 : une exportation livre-only doit pouvoir être construite depuis une liste d'inclusion.

### 3.4 Retrieval

- F-15 : la consultation doit pouvoir être textuelle et filtrable.
- F-16 : une recherche par composant, par preuve et par statut.
- F-17 : une réponse citant la source et la date.
- F-18 : la préparation futuriste pour RAG doit être optionnelle et non bloquante.
- F-19 : les graphes ne sont pas des dépendances.

## 4. Exigences non fonctionnelles

- déterministe en mode local ;
- pas de GUI obligatoire ;
- pas de dépendance au réseau ;
- pas de dépendance haute si elle existe déjà dans `deps` ;
- obsidian lisible comme un dossier normal ;
- events possible non bloquants ;
- pas de perte silencieuse ;
- permission RBAC sur routes ;
- authentification via `core/auth` et JWT ;
- mise à jour possible sans réécriture complete du historique.
- signature ADR et versions.

## 5. Compatibilité

Le backend Python reste le runtime principal. Les API FastAPI existantes, les routeurs `core_domains`, `extensions`, `security`, `knowledge`, `skills` et les interfaces WebUI/CLI/Desktop restent l'interface observable. Les tests existants sont une composante d'acceptation.

## 6. Contraintes de sécurité

- respect de `Human Root of Trust`.
- aucune mutation sans autorisation.
- aucun secret persistant.
- redaction possible pour publication.
- logs et sorties conservés avec provenance.
- opérationists hors Git main.
- RBAC existant : `core/auth` et permissions.

## 7. Critères d'acceptation

- Une architecture correspond exactement à ADR-EM-001.
- Chaque point d'intégration cite un emplacement réel du dépôt.
- Les flux sont documentés.
- Les responsabilités sont tranchées entre Rust et Python.
- Les interactions avec Obsidian, code, API et agents sont explicites.
- Obsidian demeure la source documentaire officielle.

---

Document lié : `ADR-EM-001-engineering-memory-architecture.md`.
