# ADR-4005 — Modèle de confiance des extensions (Skills, Plugins, MCP, Integrations)

**Statut** : Implémenté
**Date** : 2026-09-28
**Implémentation** :
[`core/tools/server_policy.py`](/core/tools/server_policy.py),
[`core/tools/servers.py`](/core/tools/servers.py),
[`core/skills/manager.py`](/core/skills/manager.py),
[`core/plugins/validator.py`](/core/plugins/validator.py),
[`core/knowledge/web_ingest.py`](/core/knowledge/web_ingest.py) (API publique du garde-fou SSRF),
[`interfaces/api/routers/capabilities.py`](/interfaces/api/routers/capabilities.py),
[`interfaces/api/routers/v1.py`](/interfaces/api/routers/v1.py)

---

## Contexte

Principe fondateur : **une extension est un composant non fiable par défaut** —
agent, LLM, skill, plugin, MCP, integration ou outil externe ne possède jamais
directement les secrets ni les capacités privilégiées de l'utilisateur.

Chaîne de confiance respectée (Human Root of Trust) :

```text
User (identité + volonté)
  ↓ autorisation / capability
ETHAN Core (arbitrage, échec explicite, audit)
  ↓ opération privilégiée
Extension (non fiable, exécutée sous contrôle Core)
```

L'audit du 2026-09-28 confronté au code a confirmé **trois écarts réels**
(les autres vecteurs listés dans la demande ont été recherchés puis écartés
faute de confirmation — voir § « Audit des vecteurs ») :

1. **Routes d'extension sans gate d'autorisation.** `auth_middleware` exige
   déjà un JWT sur toutes les routes non publiques, mais la permission (rôle →
   action) n'était posée que sur `POST /tools/servers`. Or le dépôt impose un
   `require_permission` par mutation (convention `domains.py`,
   `component_lifecycle.py`) : sans gate, un simple `viewer` pouvait muter des
   serveurs MCP, skills et plugins — escalade claire (« extension abuse »).
2. **Aucune politique de serveur d'outils.** `ToolServerManager.register/update`
   persistait n'importe quelle combinaison URL / transport / commande / header.
   Enchaînement confirmé : `PUT /tools/servers/{id}` sans RBAC →
   `metadata.transport="stdio"` + commande arbitraire → `POST …/sync` sans
   RBAC → **exécution d'un processus local sous l'identité du Core** ; et en
   transport http, `url` vers une IP interne ou l'IMDS cloud (**SSRF**) avec
   `follow_redirects=True`.
3. **Contrôles d'activation et de code contournables.** `SkillManager.execute`
   (Core) ne consultait pas `is_enabled` — seul le route API refusait, donc la
   désactivation n'était qu'un contrôle d'affichage pour tout appelant Core
   (autonomie, planner). Le validateur de plugins était une liste de démentis
   facilement contournable (`importlib`, `io`, `builtins`, `__builtins__`,
   `__globals__`).

## Problème

Consolider Skills, Plugins, MCP et Integrations **sans fausse sécurité** :
toute permission doit être appliquée côté Core, jamais uniquement dans une
interface ; les refus doivent être explicites, bornés, révocables et
auditables ; sans recréer de module existant (Règle absolue : éviter les
doublons) ni casser les contrats historiques (masquage des secrets,
détection MCP, loader legacy).

## Décision

### 1. Politique de serveur d'outils dans le Core (fail-closed)

Nouveau module `core/tools/server_policy.py`, appliqué par
`ToolServerManager` à **l'enregistrement**, à la **mise à jour** (record
fusionné) et **avant toute connexion** (`sync_tools` — défense en profondeur,
utile pour les records écrits avant durcissement) :

| Contrôle | Règle |
|---|---|
| Identity | `name` non vide/borné ; `auth_type` ∈ {none, bearer, oauth} ; `bearer` exige `auth_config.token` (jamais ré-échoué) |
| Transport | allowlist {http, streamable_http, stdio} ; tout autre = refus |
| stdio | `command` = chemin **absolu** présent dans `ETHAN_MCP_STDIO_ALLOWLIST` (allowlist vide ⇒ stdio désactivé) ; `args` = liste de chaînes ; `env`/`cwd` = refusés (pas d'ignoré silencieux) |
| http (SSRF) | destination **publique** par défaut (garde-fou unique `core.knowledge.web_ingest`) ; `ETHAN_MCP_ALLOW_PRIVATE_HOSTS=1` autorise loopback/RFC1918/ULA (serveurs MCP locaux) ; **link-local + endpoints de métadonnées cloud toujours refusés**, y compris en mode privé ; credentials dans l'URL refusés |
| TLS | `verify_ssl=false` refusé (pas de dégradation silencieuse) |
| Enable/disable | un serveur désactivé refuse toute `sync_tools` |

Le garde-fou SSRF existant a reçu un **point d'entrée public**
(`validate_public_url`, `is_safe_public_ip`, `resolve_hostname`) plutôt
qu'une seconde implémentation : une seule politique, un seul comportement.

### 2. RBAC posé sur toutes les routes d'extension

| Surface | Permission |
|---|---|
| `GET /v1/tools/servers[/{id}]` | `READ` |
| `POST/PUT/DELETE /v1/tools/servers…`, `…/status` | `ADMIN` |
| `POST /v1/tools/servers/{id}/sync` (connexion réseau / processus) | `EXECUTE` |
| `GET /v1/tools/pipelines[/{id}]` | `READ` ; `POST/DELETE` → `WRITE` |
| `POST /v1/skills`, `PUT/DELETE /v1/skills/{id}`, `…/toggle`, `…/valves` | `PLUGINS` |
| toutes les mutations `/v1/plugins/*` (install, enable, disable, toggle, update, delete, connect, connection) | `PLUGINS` |

Cohérent avec les conventions du dépôt (`domains.py` : WRITE sur les
mutations ; `component_lifecycle.py` : ADMIN/EXECUTE/SETTINGS) et avec
`POST /v1/skills` déjà sous `PLUGINS`. La matrice est **verrouillée par un
test introspectif** (`interfaces/api/tests/test_extensions_rbac_api.py`) :
une route qui perd son gate casse la CI.

### 3. Activation des skills arbitrée par le Core

`SkillManager.execute` refuse une skill `is_enabled=False` (erreur explicite),
quelle que soit l'origine de l'appel. Le contrôle API reste (409) mais n'est
plus la seule barrière — la décision vit dans `core/` et survit à la
disparition de toute interface.

### 4. Validateur de plugins durci (listes d'échappement fermées)

`FORBIDDEN_IMPORTS` += `importlib`, `io`, `builtins` ; nouvelles vérifications
AST `FORBIDDEN_NAMES` (`__builtins__`) et `FORBIDDEN_ATTRIBUTES`
(`__globals__`, `__subclasses__`, `__code__`). Portée déclarée honnêtement
dans le docstring : **défense en profondeur, pas un sandbox** — l'exécution de
code non fiable relève du sandbox Docker (SkillLab) et du contrôle d'accès
amont (permission `plugins`, provenance).


---

## Audit des vecteurs (demandés) — constats confrontés au code

| Vecteur | Verdict | Preuve / action |
|---|---|---|
| Secrets exposés (réponses/events) | ✅ Propre | `ToolServerManager._public_server` masque token (`{token_set}`) et `headers` (`header_keys`) ; testé (events + réponses) ; aucun `register/update` ne renvoie `auth_config` complet |
| Tokens dans logs | ✅ Propre | aucun `logger.*token/secret/api_key` avec valeur ; le `repr` de `ClientCredentials` masque le secret ; messages d'erreur MCP testés sans fuite (`test_error_message_never_leaks_token`) |
| API keys dans le frontend | ✅ Propre | grep `sk-…/AKIA…/xoxb-…/hf_…` + clés codées en dur sur `interfaces/webui/src` → zéro hit |
| Endpoints sans authorization | ⚠️ Corrigé (extension) | routes MCP/tools/skills/plugins gateées (tableau §2) ; **reste hors périmètre** : mutations `/automations`, `/channels`, `/notes`, `/prompts`, `/calendar` sans `require_permission` — identiques mais non-extensions → FIXME suivi (voir § Limites) |
| SSRF | ✅ Corrigé (MCP) | garde-fou unique réutilisé + opt-in privé + IMDS/toujours refus ; web_ingest/web_research déjà couverts ; providers OAuth = URLs déclarées par le provider (aucune URL depuis paramètres utilisateur) ; MCP `follow_redirects=True` documenté comme limite résiduelle (voir § Limites) |
| Command injection | ✅ Propre | aucun `shell=True` dans `core/`, `interfaces/api/`, `plugins/` (un seul hit = commentaire « jamais shell=True ») ; SkillLab : `create_subprocess_exec` argv figée + sandbox Docker obligatoire (aucun fallback local) |
| Path traversal / unsafe file access | ✅ Propre | aucune écriture fichier à partir d'un chemin utilisateur dans skills store ni integrations ; `resolve_safe_path` existe côté Capability.matches (docs/security §05) |
| Privilege escalation | ✅ Corrigé | chaîne critique fermée : gate `ADMIN/EXECUTE/PLUGINS` (test introspectif) + politique Core fail-closed — un `viewer`/`standard` ne peut plus ni créer un serveur MCP, ni le basculer en stdio, ni le synchroniser |
| Extension abuse | ✅ Corrigé (partiel) | allowlists transport/auth/stdio/destination ; activation skills Core ; validateur durci — le gating des *permissions déclarées* des plugins au runtime reste ouvert (§ Limites) |

## Impact (analyse demandée)

- **Core** : +1 module de politique (`server_policy`), 3 points durcis
  (`servers.py`, `skills/manager.py`, `plugins/validator.py`), API publique
  SSRF ajoutée (additive) dans `web_ingest`. Aucun doublon créé.
- **Runtime** : aucun changement (aucun composant Runtime ni contrat Event
  modifié ; événements `tool.server.*` inchangés, payload public inchangé).
- **Plugins** : le loader legacy (`plugins/loader.py`) reste un *client* du
  validator Core — il hérite du durcissement sans duplication (Première Loi).
- **Sécurité** : matrice RBAC verrouillée par test ; comportement fail-closed
  par défaut ; aucun secret déplacé ni exposé ; chaîne Human Root of Trust
  respectée (User → permission → Core → opération).
- **Maintenance** : 2 variables d'environnement documentées ; messages de
  refus actionnables (422 API) ; records legacy validés à l'exécution.

**Conformité architecture** : oui — toute la capacité (politique, RBAC, Core
enforcement) vit dans `core/` + gates API ; les interfaces ne font que
transmettre. `ComponentManager`/WebUI inchangés.

## Rétrocompatibilité opérationnelle (comportement cassant assumé)

```bash
# serveurs MCP locaux (loopback/RFC1918) :
ETHAN_MCP_ALLOW_PRIVATE_HOSTS=1
# serveurs MCP en stdio (chemins absolus, séparés par des virgules) :
ETHAN_MCP_STDIO_ALLOWLIST=/usr/bin/python3,/usr/local/bin/node
```

Sans ces variables, le Core **refuse** (422, message explicite) au lieu
d'ignorer — c'est voulu : une extension n'est pas fiable par défaut. Les
tests déclarent l'opt-in via `monkeypatch` (fixtures dédiées).

## Limites assumées (hors périmètre de cette ADR)

1. `sync_tools` MCP ne passe pas encore par `SecureToolEnforcer`
   (PolicyEngine/Capability/Exfil) — documenté `docs/security/07` §8 et
   toujours d'actualité : ici, RBAC + politique de configuration + refus
   fail-closed ont été posés, pas l'enforcement d'exécution par sujet.
2. Redirections MCP (`follow_redirects=True`) : la validation porte sur
   l'URL déclarée ; une redirection publique → privé n'est pas interceptée
   (nécessiterait un hook httpx par hop — évolution future).
3. Mutations d'extension non couvertes par ce périmètre mais confirmées
   sans gate : `/automations`, `/channels`, `/notes`, `/prompts`,
   `/calendar` (routes non-extensions du même routeur) — suivi dédié.
4. Permissions déclarées des plugins : affichées (`GET …/permissions`) mais
   encore non opposables au runtime — nécessite le câblage grant/check avec
   le PolicyEngine (RFC distincte).

## Tests

- `tests/core/test_mcp_server_policy.py` (32) : stdio allowlist, SSRF,
  opt-in privé, IMDS, schemes, credentials URL, TLS, headers, secrets,
  manager (register/update/sync revalidation, enable/disable).
- `interfaces/api/tests/test_extensions_rbac_api.py` (25) : matrice
  route → permission (introspection) + sémantique des rôles.
- `tests/core/test_skills_activation_enforcement.py` (3) : refus Core.
- `tests/test_plugin_validator.py` (+6) : échappements fermés + code
  bénin toujours accepté.
- Régessions couvertes : `interfaces/api/tests/test_mcp_servers.py`
  (opt-in fixture, secrets inchangés), `tests/core/test_domain_stores.py`,
  `tests/test_ethan_core/test_mcp_client_extended.py` (normalisation URL).

Validation : `tests/` complet (**1529 passed**, 25 skipped),
`interfaces/api/tests/` (**240 passed**), `ruff check` + `ruff format`
verts, `lint-imports` (5 contrats d'architecture : 5 kept, 0 broken).

**État audité** : 2026-09-28 — ✅ Confronté au code (3 écarts confirmés et
corrigés ; 10 vecteurs recherchés, 4 écartés faute de confirmation).

