# ETHAN TUI — Interface plein écran

Client plein écran du CLI ETHAN, construit sans nouvelle dépendance lourde
(stdlib + `rich` déjà présent). Il **ne réimplémente aucune logique métier**
(AGENTS.md, Première Loi) : agents, modèles, providers, outils, sessions et
autorisations HROT viennent tous du Core via la frontière HTTP unique
`interfaces.cli.core.client`.

## Lancement

```bash
ethan cli                          # interface plein écran
ethan cli --session <chat_id>      # reprendre une session Core
ethan cli --api-url http://host:8000 --timeout 60 --no-color
python3 -m interfaces.cli.tui      # point d'entrée module (dev)
```

## Architecture

```
interfaces/cli/tui/
├── __init__.py        exports TuiApp, main
├── __main__.py        python -m interfaces.cli.tui
├── app.py             boucle principale, rendu, slash commands, clavier
├── models.py          dataclasses typées (Agent, Model, Provider, Tool,
│                      ChatSummary, ChatMessage, ApprovalItem, StreamEvent…)
├── core_client.py     projection typée des contrats Core (GET/POST/SSE)
├── terminal.py        lecture clavier bas niveau (termios/tty/select)
└── README.md
```

Flux de données :

```
TUI (app.py) ──► TuiCoreClient (core_client.py) ──► request_json / stream_sse
                                                         │
                                                         ▼
                                                  Core API :8000
```

Le flux SSE (`/v1/chat/completions/stream`) est consommé dans un thread
secondaire (`run_stream_worker`) et projeté dans la file `stream_queue` ; la
boucle principale draine la file et met à jour l'état (`_apply_event`).

## Contrats Core utilisés

| Capacité | Route Core |
|---|---|
| Agents | `GET /v1/agents` |
| Modèles | `GET /models` |
| Providers | `GET /providers` |
| Outils | `GET /v1/tools` |
| Sessions | `GET /chats`, `GET /chats/{id}/messages`, `POST /chats` |
| Chat streaming | `POST /v1/chat/completions/stream` (SSE) |
| État | `GET /v1/state` |
| HROT / approbations | `GET /internal/approval/pending`, `POST /internal/approval/resolve` |
| HROT durable | `GET /internal/hrot/pending`, `POST /internal/hrot/requests/{id}/resolve` |

## Commandes slash

`/help`, `/exit`, `/quit`, `/new`, `/reset`, `/clear`, `/sessions`,
`/session <id>`, `/agents`, `/agent <id|nom>`, `/models`, `/model <id>`,
`/providers`, `/provider <id>`, `/tools`, `/status`, `/approve`,
`/history`, `/retry`.

## Autorisations HROT

Le TUI n'implémente aucune permission locale. Il affiche :

- pour chaque appel d'outil streamé (`tool_call`/`tool_result`), le statut
  Core (`success`, `rejected`, `failed`, `timeout`) et la raison Core ;
  un `rejected` est présenté comme un refus HROT (PolicyEngine /
  SecureToolEnforcer), jamais comme un succès ;
- le panneau `/approve` lit les demandes en attente via les contrats Core
  existants et permet d'approuver/rejeter via les routes Core.

## Limitation connue — approbation in-stream

Le Core n'émet pas encore d'événement SSE de demande d'approbation
pendant l'exécution d'un outil dans le chat : `SecureToolEnforcer.check`
rejette toute action `REQUIRE_CONFIRMATION` (fail-closed) sans créer de
requête d'approbation intermédiaire. Le TUI affiche donc le refus, mais ne
peut pas arbitrer l'exécution en cours. Contrat manquant proposé :
`permission_request` / `permission_resolved` dans le flux SSE chat, backed
par `ApprovalEngine` Core. Voir ADR-4009-cli-tui.

## Sessions

Aucun stockage de sessions indépendant : la liste et l'historique viennent
du Core (`/chats`). Au lancement, la conversation la plus récente est
reprise ; `/new` crée une nouvelle conversation côté Core au prochain
message. Quitter et relancer retrouve la dernière session.

## Tests

```bash
pytest tests/cli/ethan/tui/
```
44 tests couvrent : point d'entrée, connexion, agents/modèles, streaming,
sessions, outils, HROT, indisponibilité du Core.
```

Now add an ADR. Let me create `Obsidian/Architecture/ADR/ADR-4010-cli-tui.md` (next number after 4009). Actually 4009 is application-target-architecture. Let's use 4010.<|end|><|start|>start<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="command">
cat > /home/fatsio/AI/Ethan/Obsidian/Architecture/ADR/ADR-4010-cli-tui.md <<'EOF'
# ADR-4010 — Interface CLI/TUI ETHAN (client Core, HROT préservé)

- **Statut** : Proposed
- **Date** : 2026-11-10
- **Contexte** : Mission C1 — ETHAN CLI : fondations et première interface interactive.

## Contexte

ETHAN dispose d'un Core riche (agents, providers, modèles, outils, sessions,
HROT, approbations) exposé par l'API HTTP. Le CLI existant (`interfaces/cli`)
est un pass-through par commandes, sans interface plein écran. Il manquait
une TUI interactive comparable à OpenCode, tout en respectant la Première
Loi : ETHAN existe indépendamment de ses interfaces.

## Décision

1. **Le TUI est une interface, pas un moteur.** `interfaces/cli/tui/` ne
   contient aucune logique métier : il projette les contrats Core via la
   frontière HTTP unique `interfaces.cli.core.client`
   (`request_json`, `stream_sse`).

2. **Point d'entrée `ethan cli`.** Sans argument, `ethan cli` lance le TUI
   plein écran ; avec argument, il délègue à la commande CLI (compatibilité
   préservée). `ethan tui` est l'alias explicite.

3. **Aucune nouvelle dépendance lourde.** Le TUI utilise `rich` (déjà
   dépendance) + stdlib (`termios`, `tty`, `select`, `threading`). Pas de
   `textual`/`prompt_toolkit`.

4. **Pas de stockage de sessions indépendant.** La liste et l'historique
   viennent du Core (`/chats`, `/chats/{id}/messages`). Au lancement, la
   conversation la plus récente est reprise ; `/new` crée une conversation
   Core au prochain message.

5. **HROT préservé.** Aucune permission locale : le TUI affiche les statuts
   Core des outils (`success`/`rejected`/`failed`/`timeout`) et propose le
   panneau `/approve` backed par `/internal/approval/*` et
   `/internal/hrot/*`. Un `rejected` est présenté comme un refus HROT, jamais
   comme un succès.

6. **Streaming dans un thread secondaire.** Le flux SSE est consommé hors du
   thread principal et projeté dans une file ; la boucle principale draine la
   file et met à jour l'état. L'annulation utilise un `threading.Event`
   propagé à `stream_sse` (paramètre `abort_event`, optionnel, rétro-
   compatible).

7. **Correction ciblée de l'authentification locale.** `get_token()` valide
   l'expiration du token legacy (`~/.config/ethan/config.json`) avant de
   l'adopter, pour ne pas masquer le bootstrap local (`create_local_token`).

## Contrat manquant identifié

Le Core n'émet pas d'événement SSE de demande d'approbation pendant
l'exécution d'un outil dans le chat : `SecureToolEnforcer.check` rejette
toute action `REQUIRE_CONFIRMATION` (fail-closed) sans créer de requête
d'approbation intermédiaire. Le TUI affiche donc le refus, mais ne peut
pas arbitrer l'exécution en cours.

Contrat proposé (non implémenté, à valider avant modification Core) :
- événements SSE `permission_request` / `permission_resolved` dans
  `/v1/chat/completions/stream`, backed par `ApprovalEngine` Core ;
- routes existantes `/internal/approval/pending` et `/internal/approval/resolve`
  réutilisées par le panneau `/approve`.

Cette modification Core est volontairement hors de la mission C1 pour éviter
une refonte de la frontière de sécurité ; elle est documentée comme
limitation.

## Conséquences

- Nouveau paquet `interfaces/cli/tui/` (6 modules) + commande `tui`/`cli`.
- 44 tests dédiés (`tests/cli/ethan/tui/`) : entrée, connexion, agents/
  modèles, streaming, sessions, outils, HROT, indisponibilité Core.
- `stream_sse` gagne un paramètre optionnel `abort_event` (rétro-compatible).
- `get_token()` tolère les tokens legacy expirés.

## Alternatives rejetées

- Forker OpenCode (interdit par la mission).
- Intégrer le moteur d'agents d'OpenCode (interdit).
- Utiliser `textual`/`prompt_toolkit` (nouvelle dépendance lourde sans
  justification ; `rich` + stdlib suffisent).
- Stocker les sessions localement (viole la Première Loi).
EOF
echo "written"