# ADR-4010 — Interface CLI/TUI ETHAN et approbation HROT in-stream

- **Statut** : Implemented (Core + TUI + WebUI)
- **Date** : 2026-11-10

## Contexte

ETHAN dispose d'un Core riche exposé par l'API HTTP. Le CLI existant est un
pass-through par commandes, sans interface plein écran. Il manquait une TUI
interactive comparable à OpenCode, tout en respectant la Première Loi.

## Décision

1. **Le TUI est une interface, pas un moteur.** `interfaces/cli/tui/` ne
   contient aucune logique métier : il projette les contrats Core via la
   frontière HTTP unique `interfaces.cli.core.client`.

2. **Point d'entrée `ethan cli`.** Sans argument, lance le TUI plein écran ;
   avec argument, délègue à la commande CLI (compatibilité préservée).
   `ethan tui` est l'alias explicite.

3. **Aucune nouvelle dépendance lourde.** `rich` + stdlib uniquement.

4. **Pas de stockage de sessions indépendant.** Liste/historique via le Core.

5. **HROT préservé.** Aucune permission locale.

6. **Approbation HROT in-stream.** Contrat `permission_request` /
   `permission_resolved` dans le flux SSE chat, backed par `ApprovalEngine`
   Core. `SecureToolEnforcer.check` accepte `approved=True` pour traiter
   `REQUIRES_CONFIRMATION` comme `ALLOW` après approbation valide, sans
   contourner capacité/exfiltration. Refus par défaut en cas d'erreur.

## Garanties de sécurité vérifiées

- Aucun contournement de HROT : la décision vient de `ApprovalEngine`.
- Aucune exécution avant approbation valide.
- Refus par défaut en cas d'erreur/incertitude/déconnexion.
- Les contrôles de capacité et d'exfiltration restent appliqués après
  approbation.

## Fichiers modifiés (principaux)

- `core/approval/engine.py` : `create_request`, `await_decision`, `get_request`.
- `core/security/integration.py` : paramètre `approved` sur `check()`.
- `core/tools/executor.py` : paramètre `approved` propagé.
- `core/chat/pipeline.py` : `set_approval_engine`, `set_policy_enforcer`,
  `get_policy_enforcer`, paramètre `approved` sur `execute_tool_call`.
- `interfaces/api/routers/v1.py` : flux d'approbation in-stream.
- `interfaces/api/main.py` : injection de l'approval engine et du policy
  enforcer dans le pipeline.
- `interfaces/cli/tui/models.py`, `core_client.py`, `app.py` : événements
  `permission_request`/`permission_resolved`, affichage et résolution.
- `interfaces/webui/src/.../use-chats.ts` : gestion des deux événements.

## Tests

- 44 tests TUI verts.
- `tests/test_chat_stream_api.py` : 2 passed.
- `tests/core/test_approval_hrot_integration.py` : 4 passed.
- import-linter : 5 contrats kept.