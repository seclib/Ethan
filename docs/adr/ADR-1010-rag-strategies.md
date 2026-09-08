# ADR-1010 — Sélection de la stratégie de recherche RAG

## Date
2026-09-04

## Statut
✅ **Implémenté**

---

## Résumé

L'utilisateur peut choisir la **stratégie de recherche RAG** appliquée par
ETHAN, avec deux niveaux de configuration :

- **globale** (défaut du moteur, persistée dans `rag-config`) ;
- **par collection** (surcharge individuelle, résolution effective
  `collection > globale > auto`).

Décisions structurantes :

- **Un seul moteur RAG** : une stratégie est une *configuration* du chemin de
  code unique de `core/rag/retrieval.py` — jamais un second système ;
- **Catalogue fondé sur les capacités réelles** : seules les stratégies mappées
  sur un chemin existant sont exposées (`auto`, `keyword`, `semantic`,
  `hybrid`). Le reranking, qui n'existe pas dans ETHAN, n'est pas exposé ;
- **Recommandation calculée par le Core** (`recommend_strategy`) sur l'état
  réel du moteur (embeddings réels ou mock) — les interfaces ne font que
  l'afficher ;
- **Double validation** : stricte côté API (`ValueError` → HTTP 422, l'admin ne
  doit pas enregistrer une stratégie fantôme), fail-safe côté moteur
  (`normalize_strategy` → défaut, un tiers ne doit jamais casser la recherche).

---

## Modifications

### 1. Stratégies (`core/rag/strategies.py`)

**Ajouté:**
- `recommend_strategy(has_real_embeddings)` — recommandation fondée sur les
  capacités réelles (`hybrid` si embeddings réels, `auto` sinon) ;
- `get_strategy` strict (lève `ValueError` sur identifiant inconnu).

### 2. Pipeline (`core/rag/pipeline.py`)

**Ajouté:**
- `RAGPipeline.recommend_strategy()` — recommandation de l'instance moteur ;
- clé `recommendation` additive dans `stats()`.

### 3. API (`interfaces/api/routers/v1.py`)

**Ajouté:**
- `GET /v1/rag/strategies` — catalogue + défaut + recommandation du Core ;
- `strategy` accepté par `PUT /v1/rag/config` (validation stricte 422) ;
- `retrieval_strategy` accepté par `POST /v1/knowledge/collections`.

**Corrigé:**
- `update_rag_config` : `RAGPipeline.configure()` est désormais `await` (la
  coroutine n'était jamais attendue — la config n'était pas appliquée).

### 4. WebUI (rendu uniquement, aucune logique métier)

- Catalogue et recommandation lus depuis `GET /v1/rag/strategies` — aucune
  stratégie inventée côté interface ;
- Sélecteur de stratégie globale (Settings → RAG) avec recommandation ETHAN ;
- Sélecteur à la création d'une collection + changement à chaud dans son
  détail ; avertissement ambre quand la stratégie choisie dépend des
  embeddings et que le moteur n'en a pas (dégradation annoncée).

### 5. Documentation

- `docs/user-guide/rag-strategies.md` — guide utilisateur (stratégies,
  dégradation, recommandation, endpoints) ;
- Navigation MkDocs mise à jour.

---

## Contrat d'extension (stratégie future, ex. reranking)

1. Implémenter le chemin de code réel dans `core/rag/retrieval.py` ;
2. Ajouter une entrée `RAGStrategy` dans `_STRATEGIES` (+ id dans
   `_STRATEGY_IDS`) — le catalogue, l'API et la WebUI le découvrent sans
   modification supplémentaire ;
3. Étendre `RAGRetrieval.retrieve` (dispatch) et `recommend_strategy` si la
   capacité change la recommandation ;
4. Tester la stratégie sur son chemin réel (`tests/test_rag_strategies.py`).

**Interdit** : exposer une stratégie sans chemin de code réel dans le Core
(anti-stratégie fantôme), ou implémenter la logique dans une interface.

---

## Tests

- `tests/test_rag_strategies.py` — 11 tests : catalogue (jamais de reranking),
  validation stricte / normalisation fail-safe, chaque stratégie sur son chemin
  réel (keyword sans embeddings, semantic via synonymes sans recouvrement
  lexical, hybrid avec démonstration RRF, auto avec dégradation), persistance
  de la config globale, résolution effective par collection, rejet des
  stratégies inconnues, recommandation cohérente avec les capacités réelles ;
- `interfaces/api/tests/test_rag_strategies.py` — 4 tests : route catalogue +
  recommandation, création/mise à jour de collection avec stratégie (422 si
  inconnue), `PUT /rag/config` avec `strategy` (422 si inconnue, persistance
  vérifiée), retrieve réel appliquant la stratégie effective de la collection.
