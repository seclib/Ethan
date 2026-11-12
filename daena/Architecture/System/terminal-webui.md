# Terminal WebUI — PTY distant servi par ETHAN Core

> Statut : implémenté · CLI équivalent : `interfaces/cli/`

## 1. Ce que le terminal n'est PAS

Le terminal WebUI **n'est pas un deuxième CLI**. Il ne réimplémente aucune
commande ETHAN et ne possède aucune logique métier :

```
Terminal WebUI (xterm.js, rendu seul)
        │  WebSocket /v1/terminal/ws + REST /v1/terminal
        ▼
ETHAN API (interfaces/api/routers/terminal.py — passerelle mince)
        ▼
TerminalService (core/terminal/) ← logique, sécurité, état, processus
        ▼
PTY réel (forkpty) → $SHELL
```

Une commande ETHAN tapée dans ce terminal (`ethan status`, `ethan extension
list`, …) part dans le même shell, appelle la même API et le même Core que
lorsqu'on la tape dans `interfaces/cli/`. **Aucun doublon d'implémentation.**

## 2. Choix d'audit : pourquoi un vrai PTY

Deux mécanismes existants ont été écartés après examen :

| Mécanisme existant | Pourquoi insuffisant |
|---|---|
| `plugins/terminal/` | Exécuteur **one-shot** à liste blanche : renvoie stdout/stderr d'UNE commande et meurt. Pas de session, pas de stdin, pas de Ctrl+C. |
| `interfaces/api/routers/realtime.py` | Pont **WebSocket ↔ NATS** pour les événements. Aucun processus, aucun PTY. |

Un terminal interactif exige un **pseudo-terminal** et un flux bidirectionnel
persistant : d'où `os.forkpty()` + WebSocket. Le subprocess HTTP « one-shot »
est explicitement écarté — il ne peut ni afficher un prompt, ni recevoir un
Ctrl+C, ni survivre à une reconnexion.

## 3. Contrat d'interface

WebSocket `/v1/terminal/ws` (JSON dans les deux sens) :

| Sens | Message | Effet |
|---|---|---|
| → serveur | `{"type":"input","data":"…"}` | stdin ; `\x03` = Ctrl+C |
| → serveur | `{"type":"resize","cols":N,"rows":N}` | `ioctl TIOCSWINSZ` |
| → serveur | `{"type":"interrupt"}` | SIGINT explicite au groupe |
| → serveur | `{"type":"ping"}` | keepalive |
| → client | `{"type":"session", …}` | état initial (vocabulaire Core) |
| → client | `{"type":"output","data":"…"}` | octets PTY, **ANSI conservés** |
| → client | `{"type":"exit","exit_code":N}` | fin réelle du processus |
| → client | `{"type":"error","code":…}` | erreur Core, code stable |

REST : `POST /sessions`, `GET /sessions`, `GET /sessions/{id}`,
`POST /sessions/{id}/input|resize|interrupt`, `DELETE /sessions/{id}`.

## 4. Sécurité (fail-closed)

| Garde-fou | Mise en œuvre |
|---|---|
| Pas de root | `assert_not_root()` : si le service tourne en `geteuid()==0`, la session est **refusée** (403). ETHAN ne fournit ni root, ni sudo. |
| Pas de fuite de secrets | L'environnement du shell est une **allowlist** (`build_clean_env`) : `ETHAN_TOKEN`, `*_API_KEY`, `*_PASSWORD`, `*_SECRET`… ne sont jamais transmis. |
| Répertoire borné | `resolve_safe_path` (garde-fou Core existant) : toute tentative de `../` ou de sortie de racine retombe sur la racine. |
| Permissions | Session = `Permission.EXECUTE` : rôle `admin` seul. `viewer`/`user`/`standard` sont refusés (403). |
| WebSocket authentiqué | `auth_middleware` est HTTP-only ; le WS vérifie **explicitement** le JWT (4401) et la permission (4403) **avant** `accept()`. |
| Docker illimité | Aucun accès automatique : le terminal est le shell du compte du service, rien de plus. |
| Token WS en query | Les WS navigateur ne portent pas d'en-tête : `?token=` est obligatoire (fallback cookie `ethan_token`). JWT court + **WSS exigé en prod** (un token en query peut finir en log serveur/proxy). |

Les commandes **privilégiées** passent par le mécanisme d'autorisation
d'ETHAN : la RBAC de l'API, pas un contournement local.

## 5. Cycle de vie

- **Déconnexion ≠ mort** : fermer l'onglet ne tue pas le shell ; la session
  reste listée et se réattache via `?session_id=`.
- **Redémarrage de l'API** : les processus meurent avec l'API ; le registre
  repart vide et `shutdown_all()` garantit l'absence d'orphelin.
- **Ctrl+C** : la ligne discipline du PTY transforme `\x03` en SIGINT pour le
  groupe de processus — comportement natif, aucun cas particulier serveur.
- **Nettoyage** : les sessions mortes sont récoltées (`waitpid`) et purgées ;
  le FD maître est toujours fermé.

## 6. Limites assumées

- `workers=1` obligatoire : le registre est en mémoire, une session appartient
  au worker qui l'a créée (c'est déjà le cas du déploiement).
- La vue est **une seule session active à l'écran** ; les autres sont
  listées et réattachables (le multi-panneau n'est pas implémenté).
- Le scrollback n'est pas rejoué après reconnexion (le shell continue, son
  historique local part avec la page).