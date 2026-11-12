# Capacités optionnelles — validation runtime

Date : 2026-11-04

## Résultats effectifs

### Qdrant
- image officielle : `qdrant/qdrant` version du jour (`latest`, 8a80c5500151)
- test réel : `/readyz` = `all shards are ready`
- conteneur démarré avec `--network none` et stockage persistant
- aucune intégration ETHAN finale automatisée dans cette phase
- statut : VALIDATED au niveau paquet/container

### ChromaDB
- venv isolé : `/home/fatsio/.local/share/ethan/isolated/chromadb`
- `chromadb` importé version `1.5.9`
- statut : VALIDATED à l'import local

### LangChain
- venv isolé : `/home/fatsio/.local/share/ethan/isolated/langchain`
- `langchain` importé version `1.4.8`
- statut : VALIDATED à l'import local

### LangGraph
- venv isolé : `/home/fatsio/.local/share/ethan/isolated/langgraph`
- `langgraph` importé avec succès (`version` namespace non expose)
- statut : PARTIELLEMENT VALIDATED au niveau import; aucune verification fonctionnelle supplementaire

## Limites globales

- pas encore d'integration dans settings via installation automatique dans cet environnement;
- pas de HROT runtime demontre pour ces capacites;
- pas de test WebUI Playwright;
- declaration Core uniquement, declaree pas installee par defaut.

## Conclusion

La disponibilite reelle a ete prouvee pour Qdrant et pour les imports locaux LangChain/ChromaDB. Certification complete reste non demontree pour le parcours install frontend.

Statut global associe : PARTIALLY_VALIDATED.
