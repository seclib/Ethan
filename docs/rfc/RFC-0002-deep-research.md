# RFC-0002 — Deep Research ETHAN

## Date
2026-08-24

## Statut
✅ **Implémenté** — voir les sections ci-dessous pour l'architecture livrée.

## Résumé
Recherche approfondie multi-étapes : planification de requêtes,
exploration web itérative, synthèse sourcée et rapport final —
orchestrée par le Runtime comme une mission, rendue par la WebUI.

## Origine
Odysseus (research/, researchSynapse.js). ETHAN possède déjà les
briques : tool `builtin_web_search`, missions avec étapes vérifiées
(`/v1/missions`), RAG pour le cache. Il manque l'orchestrateur.

## Architecture cible
```
core/research/              ← ResearchPlanner + ResearchSynthesizer (LLM replaceable)
runtime/                    ← exécution des étapes via Event Bus (mission runner)
interfaces/api/routers/…    ← POST /v1/research (créer), GET /v1/research/{id} (statut/rapport)
interfaces/webui /research  ← UI : lancement, progression temps réel (WS), rapport sourcé
```

## Portée proposée
1. **Core** — `ResearchManager` : décomposition de la question en
   sous-requêtes, agrégation des résultats web + knowledge interne,
   citations obligatoires, budget tokens/coût par run.
2. **Runtime** — chaque étape est un événement ; approbation humaine
   possible avant synthèse finale (réutilise `/approval/pending`).
3. **API** — cycle de vie research-run : created → planning →
   searching → synthesizing → done/failed, observable par events.
4. **WebUI** — page `/research` : formulaire de question, timeline des
   étapes, rapport markdown avec sources cliquables.

## Hors portée
- Crawl massif/scraping générique (limiter aux APIs de recherche).
