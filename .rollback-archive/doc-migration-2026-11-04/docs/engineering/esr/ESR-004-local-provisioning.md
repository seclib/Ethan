# ESR-004 — Local Provisioning (Python, exécutables, intégrés)

**Statut** : Python, exécutables, intégrés et **paquets Node implémentés** ;
modèles locaux **non implémentés** (hors périmètre — voir §5)
**Date** : 2026-09-23
**Décision parente** : [ADR-4002](/docs/architecture/adr/ADR-4002-install-on-demand.md)
**Code** : [`core/capability_manager/backends.py`](/core/capability_manager/backends.py)

---

## 1. Backend `python_package` (implémenté)

Actions allowlistées : `pip_install`, `pip_uninstall`, `verify_import`.

- **pip de l'interpréteur du Core** : `_PIP = [sys.executable, "-m",
  "pip"]` — jamais un `pip` arbitraire du PATH (risque d'interpréteur
  différent ou falsifié).
- **Paquets figés** : la spec déclare les versions exactes
  (ex. `chromadb==0.6.3`) ; l'utilisateur ne choisit pas de version
  libre (champ `choices` du schema seulement quand pertinent).
- **Vérification réelle** : `verify_import` importe le module dans le
  process (échec → rollback) ; la détection utilise
  `importlib.util.find_spec` sans importer.
- **Rollback install** : `pip uninstall -y` des paquets posés.

Cas d'usage actuel : `chromadb` (backend local, données dans
`~/.local/share/ethan/chromadb` déclarées en `data_resources`).

## 2. Backend `executable` (implémenté)

Actions : `verify_path` (présence dans le PATH via `shutil.which`),
`note`. Pas d'installation réelle : la capability est fournie par un
binaire déjà présent ; son absence produit un échec explicite.

## 3. Backend `builtin` (implémenté)

Composants **intégrés au process Core** : aucune action système,
installation/désinstallation = no-op, santé vérifiée par le check
`builtin` (process vivant). Cas d'usage : `memory` (backend vectoriel
in-process). Voir [ESR-001](/docs/engineering/esr/ESR-001-capability-model.md) §7.

## 4. Backend `node_package` (implémenté)

Actions allowlistées : `npm_install`, `npm_uninstall`, `verify_binary`.

- **npm résolu côté Core** : `shutil.which("npm")` au moment de l'usage —
  jamais un chemin fourni par l'utilisateur. npm absent → échec explicite
  (« ETHAN n'installe jamais Node lui-même », même règle que Docker).
- **Préfixe géré par ETHAN** : `~/.local/share/ethan/node` (`--prefix`),
  donc jamais `/usr/lib/node_modules` : aucun `sudo`, aucun paquet système
  touché, désinstallation propre.
- **Paquets figés** : la spec déclare la version exacte
  (ex. `@modelcontextprotocol/server-filesystem@2026.8.31`) ; l'utilisateur
  ne choisit ni paquet ni version.
- **Vérification réelle** : `verify_binary` exige la présence du binaire
  **et** son bit exécutable dans `<prefix>/bin` — la détection ne suppose
  jamais qu'un paquet npm est utilisable.
- **Rollback install** : `npm uninstall --global --prefix` des paquets
  posés par l'installation échouée (version retirée du nom).

Cas d'usage actuel : `mcp-filesystem` (serveur MCP officiel, transport
stdio, type `mcp_server`) — le binaire installé est lancé à la demande par
le client MCP d'ETHAN ([`core/tools/mcp_client.py`](/core/tools/mcp_client.py)),
d'où l'absence d'actions start/stop (aucun processus permanent).
Limite connue : aucun health check fonctionnel n'est déclarable (pas
d'endpoint permanent) — le composant reste `INSTALLED`, jamais un faux
`READY`.

## 5. Modèles locaux — **non implémenté**

Le téléchargement de modèles (LLM/embedding) n'est **pas** géré par le
capability manager. Il existe ailleurs dans ETHAN, hors de ce système :
`core/deployment/scripts/install/pull-model.sh` et le provider Ollama.
Une intégration future exposerait un composant de type `model` avec des
health checks fonctionnels (inférence test), sans dupliquer la logique.

## 6. Limites et risques

| Risque | Mitigation actuelle |
|---|---|
| Mutation de `site-packages` partagé (pas de venv dédié) | pip de l'interpréteur du Core, versions figées, rollback ; **limite documentée** : le déploiement conteneurisé isole l'environnement |
| Conflits de dépendances pip | Versions épinglées par spec ; échec explicite + rollback |
| Binaire présent mais incompatible | Health checks fonctionnels obligatoires pour READY (pas de confiance aveugle dans la présence) |
| Données locales orphelines | `data_resources` déclarés + sémantique uninstall/delete de [ADR-4003](/docs/architecture/adr/ADR-4003-data-lifecycle.md) |
| Exécution de code arbitraire via « packages » | Impossible : les paquets viennent de la spec développeur, jamais de l'input utilisateur |