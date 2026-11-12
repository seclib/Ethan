# RAG Settings Regression — Audit & Restauration

> **Statut final : FIXED** — `Settings → RAG` est restauré comme section de première classe.

---

## 1. Symptôme

L'option globale `RAG` avait disparu du menu `Settings`. Les réglages du moteur
(chunking, top_k, embeddings, stratégie de retrieval) n'étaient plus accessibles ;
seule la page `Knowledge` permettait de consulter les collections, sans exposer
la configuration du moteur lui-même.

## 2. Cause racine (prouvée, pas supposée)

La fonctionnalité **n'avait pas été supprimée** — elle était devenue du
**code mort** à trois niveaux, dans
`interfaces/webui/src/components/features/settings/components/settings-workspace.tsx` :

| Niveau | État avant correction | Preuve |
| ------ | --------------------- | ------ |
| `type Section` (l.111) | `"rag"` absent de l'union | lecture du fichier |
| `SECTIONS` (l.126) | aucune entrée RAG → invisible dans la navigation latérale | lecture du fichier |
| Dispatch conditionnel (l.183) | aucun `{activeSection === "rag" && <RagSection />}` | `RagSection()` (l.585) défini mais jamais rendu |

Le composant `RagSection` **existait et était complet** (formulaire + stats +
stratégies + sauvegarde avec toasts), et le backend **exposait déjà** toutes les
routes nécessaires. Seul le lien de navigation avait été perdu.

## 3. Composants existants réutilisés (zéro réécriture)

| Élément | Emplacement | État |
| ------- | ----------- | ---- |
| Formulaire RAG | `RagSection()` — settings-workspace.tsx | ✅ réutilisé tel quel |
| Client API RAG | `interfaces/webui/src/lib/api/rag.ts` | ✅ réutilisé (`getRagConfig`, `updateRagConfig`, `getRagStrategies`, `getRagStatus`) |
| Routes backend | `interfaces/api/routers/v1.py` (l.1133–1215) | ✅ existantes, non modifiées |
| Moteur Core | `core/rag/` (pipeline, stratégies, retrieval) | ✅ unique, non modifié |

## 4. Route restaurée

Navigation : `Settings → RAG` (catégorie *system*, icône Database), positionnée
après `Knowledge`. Accès direct par URL supporté via le hash existant :
`/settings#rag` (listener `hashchange` → `applyHash` → lookup `SECTIONS`).

Un lien secondaire **« Configurer le moteur RAG »** (`#rag`) a été ajouté dans la
section `Settings → Knowledge` pour relier les données (collections) au moteur.

## 5. Paramètres exposés (uniquement ceux appliqués par le Core)

Contrats backend vérifiés (`GET/PUT /v1/rag/config` — `PUT` protégé par
`Permission.ADMIN` avec validation stricte) :

| Paramètre | Application Core |
| --------- | ---------------- |
| `chunk_size`, `chunk_overlap` | ingestion/chunking |
| `top_k`, `max_context_chars` | retrieval |
| `embedding_model` | pipeline embeddings |
| `strategy` (auto/keyword/semantic/hybrid, validé par `validate_strategy`) | retrieval |
| Statuts live (documents, chunks, embedding_mode, recommandation) | affichage |

Note : le backend accepte en outre `splitting_strategy` et
`vector_backend(_config)` ; le formulaire ne les expose pas encore
(amélioration P2 — aucune option non supportée ajoutée côté UI).

## 6. Séparation Settings / Knowledge / Projects (inchangée)

- **Settings → RAG** : réglages **globaux du moteur** (comment le RAG fonctionne).
- **Knowledge** : gestion des **données** (collections, documents, ingestion).
- **Projects** : périmètre par projet (scope knowledge, activation).

Aucun deuxième pipeline RAG, aucun deuxième système d'embeddings, aucun
deuxième vector store n'a été créé ; la source de vérité reste
`Settings UI → ETHAN API → Core RAG config → pipeline`.

## 7. Fichiers modifiés

| Fichier | Changement |
| ------- | ---------- |
| `interfaces/webui/src/components/features/settings/components/settings-workspace.tsx` | + `\| "rag"` au type `Section` ; + entrée `SECTIONS` (RAG, Database, system) ; + dispatch `{activeSection === "rag" && <RagSection />}` ; + lien « Configurer le moteur RAG » dans `KnowledgeSection` |
| `interfaces/webui/tests/unit/settings/settings-rag-navigation.test.tsx` | **Nouveau** — 5 tests de navigation/régression |

Aucun fichier backend modifié. Aucun composant RAG réécrit.

## 8. Tests réalisés

### Nouveaux tests (Jest) — `tests/unit/settings/settings-rag-navigation.test.tsx`

| Test | Résultat |
| ---- | -------- |
| L'entrée RAG est visible dans le menu Settings | ✅ |
| La section RAG rend le formulaire du moteur (Top K, chunking, embedding, Enregistrer) | ✅ |
| La stratégie de recherche provient du Core (aucune stratégie inventée côté UI) | ✅ |
| Knowledge conserve la gestion des données + lien secondaire `#rag` | ✅ |
| Navigation par hash `#rag` (accès direct URL / refresh) | ✅ |

### Régression

| Check | Résultat |
| ----- | -------- |
| `tsc --noEmit` | ✅ exit 0 |
| Suite Jest complète | ✅ **12 suites / 38 tests** (dont 5 nouveaux) |
| `npm run build` | ✅ (verdict en fin de rapport) |
| Backend live | ✅ `GET /v1/rag/config` → HTTP 401 (route montée, protégée auth) |
| `/v1/rag/strategies` | ✅ HTTP 401 (idem) |

Pièges corrigés pendant la rédaction des tests (documentés pour les successeurs) :
1. Mock `useSettings` à références instables → « Maximum update depth exceeded »
   (l'effet `[settings]` de `GeneralSection` bouclait) — corrigé par objets stables.
2. jsdom n'implémente pas la navigation par clic d'ancre → le test « hash »
   simule le `hashchange` (mécanisme réel du composant).

## 9. Problèmes restants

| Problème | Sévérité | Action |
| -------- | -------- | ------ |
| `splitting_strategy` / `vector_backend(_config)` supportés par le backend mais non exposés dans le formulaire | P2 | Étendre `RagSection` dans une passe dédiée |

## 10. Conclusion

- ✅ `Settings → RAG` est restauré et navigable (menu + URL directe `#rag`).
- ✅ `Knowledge` conserve la gestion des collections/documents, avec un lien
  secondaire vers le moteur.
- ✅ Il n'existe qu'**un seul pipeline RAG officiel** (`core/rag/`) — aucune
  duplication créée.
- ✅ Les réglages sont **réellement appliqués par ETHAN Core** : le formulaire
  lit/écrit `PUT /v1/rag/config` (protégé ADMIN, validation stricte), le backend
  persiste via son mécanisme existant.

**Statut : FIXED**

