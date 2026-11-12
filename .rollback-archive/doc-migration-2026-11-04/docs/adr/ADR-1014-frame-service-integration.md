# ADR-1014 — Service Frame dans ETHAN (modèle ODIN)

- Statut : Implémenté
- Contexte : Frame (fork HyperFrames) est une application indépendante et doit être pilotée comme service externe confiné.
- Décision :
  - `core/plugins/frame.py` réutilise `core/plugins/compose_service.py`;
  - API `interfaces/api/routers/frame.py`, routes `/v1/plugins/frame/*`;
  - bind loopback port `5190`;
  - compose dédié `examples/frame/compose.yaml`;
  - lifecycle start/stop/restart/install/uninstall/logs/health/status;
  - ouverture Studio via URL retournée par l'état, jamais commande Docker depuis frontend.
- Sécurité : authentification et RBAC `READ`/`PLUGINS`; pas de socket Docker côté navigateur.
- Non régression : ODIN reste présent.
