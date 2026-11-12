# OPTIONAL CAPABILITIES — Conception installation et découvrabilité

## 1. Audit de l'existant

- Capacites declarees dans `core/capability_manager/builtin.py`.
- ChromaDB backend Python expose deja par `core/memory/chromadb_backend.py`.
- Qdrant backend Python expose deja par `core/memory/qdrant_backend.py`.
- LangChain et LangGraph sont deja declarees comme capacites optionnelles.
- Il existe un systeme de lifecycle et healthchecks dans `core/capability_manager`.

## 2. Strategie par type

### Qdrant
- source officielle GitHub (Qdrant)
- moteur de Vector Store Docker Compose officiel
- persist sous volume dedie
- demarrage HROT et healthcheck endpoints

### ChromaDB
- source officielle (Chroma)
- pip package dans un environnement isole si possible
- data locale `~/.local/share/ethan/chromadb`
- health endpoint

### LangChain / LangGraph
- source officielle PyPI / GitHub
- paquets python versionnes dans l environnement ETHAN user
- pas de service dedie permanent
- import verifie
- Integration large via applications autorises
- autorisation HROT

## 3. Emplacements

- sources / code : non stocké Git
- environment : venv ou poetry env / installation Core user
- config : `core/ethan_config` et capability manager
- données : `~/.local/share/ethan/chromadb`, qdrant data volumes
- aucune donnée sensible dans repo

## 4. Installation reproductible

1. Verifier presence reelle via `verify_import` ou env/volume.
2. Verifier paquets avec exact versions.
3. Executer un health check reelle.
4. Enregistrer version et chemins si state store.
5. Distinguer disponible, instale, pret.
6. Aucun restart Linked sans utilisateur ou scheduled.

## 5. Etats

- `AVAILABLE`: supporté mais non installé
- `INSTALLING`
- `INSTALLED`
- `VERIFIED`
- `INTEGRATED`
- `RUNNING` seulement services Docker
- `STOPPED`
- `FAILED`

## 6. Tutoriels de secours

- Si pip install echoue temps, offrir les instructions officielles.

## 7. Limites

- installation et permissions Python complexes;
- HROT sur container services doit rester en place;
- WebUI detection depend backend.

## Conclusion

La base actuelle est appropriee. On doit maintenant implémenter la verification et la documentation utilisateur, non une nouvelle couche de catalogue.
