# 08 — Durcissement du plan de contrôle (RBAC) & politique d'egress

> Statut : **implémenté** — gates RBAC du plan de contrôle complétés, et
> politique de destination sortante unifiée dans `core/security/egress.py`.

Ce document couvre deux invariants de frontière découverts lors de l'audit :

1. **Qui peut piloter ETHAN** — le plan de contrôle ne doit pas être modifiable
   par un rôle authentifié quelconque (section 1).
2. **Où ETHAN a le droit d'aller** — une seule politique d'egress, partagée
   (section 2).

---

## 1. Plan de contrôle vs plan de données

Définition appliquée (cf. AGENTS.md — « les interfaces révèlent ETHAN ») :

| Plan | Contenu | Exigence |
|---|---|---|
| **Contrôle** | providers, config, cookbook, agents, automatisations, skills, plugins, MCP, cycle de vie des composants | `require_permission(...)` obligatoire sur **chaque mutation** |
| **Données** | chat, notes, calendrier, prompts, canaux, RAG/knowledge, mémoire, objectifs, missions, research, vision/transcription | JWT valide suffit (`auth_middleware`) |

Règle de symétrie : *si créer une ressource exige une permission, la modifier,
la supprimer, la déclencher et l'exporter exigent la même*. L'asymétrie
constatée (création gate, mutation ouverte) était une escalade de privilège :
un rôle « viewer » pouvait réécrire un agent ou installer une recette.

### Gate par introspection, pas par convention

`require_permission` publie la permission exigée sur la closure
(`permission_checker.permission`) : un audit ou un test peut relire la matrice
« route → permission » **sans exécuter le gate**. C'est ce que fait
`interfaces/api/tests/test_privileged_control_plane_rbac.py`, qui vérifie
aussi l'inverse (le plan de données ne doit **pas** être sur-gaté, sinon un
rôle `viewer` perdrait sa propre vision/transcription/2FA).

Comptes utilisateurs : `security.py` utilise un contrôle de rôle explicite en
corps de route (`_require_admin` / `_ensure_not_self`) — volontairement
conservé, car il porte aussi les garde-fous « dernier admin » et
« pas d'action sur soi-même », que `require_permission` n'exprime pas. Le test
verrouille la présence de ce contrôle par inspection de la source.

---

## 2. Politique d'egress unique

### Problème

Trois surfaces configurables établissent une connexion sortante : serveurs MCP
(`core/tools/server_policy.py`), providers LLM (`core/llm/provider_factory.py`)
et ingestion web (`core/knowledge/web_ingest.py`). Chacune réécrivait sa
vérification d'adresse. Deux politiques = deux comportements, et la plus
permissive gagne : une surface bloquait les métadonnées cloud, l'autre non.

### Solution

`core/security/egress.py` est **la** politique : toute nouvelle fonctionnalité
qui ouvre une connexion vers une destination fournie par configuration
**doit** l'importer, jamais réimplémenter une liste d'interdits.

| Fonction | Niveau | Usage |
|---|---|---|
| `assert_literal_destination(url)` | littéral, **sans DNS** | endpoints configurés par un rôle authentifié (providers LLM) : les noms internes (`ollama`, `vllm`) ne sont pas résolubles, une résolution ferait échouer le démarrage |
| `validate_egress_url(url, allow_private=...)` | complet, **avec DNS** | destinations non fiables (serveurs MCP) : `False` = public uniquement, `True` = loopback/RFC1918/ULA tolérés |
| `is_forbidden_address(ip)` | classe « toujours interdite » | métadonnées cloud + link-local, y compris IPv4-mapped IPv6 |
| `resolve_destination_addresses(host, resolver)` | résolution fail-closed | résolveur injectable (tests hors réseau) |

Classe **toujours interdite**, même en mode privé explicitement demandé :

```
169.254.169.254, fd00:ec2::254, 100.100.100.200   (métadonnées cloud)
metadata.google.internal, metadata.goog
toute adresse link-local (IPv4/IPv6, y compris ::ffff:169.254.169.254)
schéma ≠ http(s), credentials inline dans l'URL
```

Justification : une destination détournée vers le point de contact des
métadonnées retourne les credentials de l'instance hôte — l'issue SSRF la plus
grave. Les credentials dans l'URL sont refusés par construction : les secrets
vivent dans la couche dédiée (cf. AGENTS.md — « secret »).

---

## 3. Fichiers

- `core/security/egress.py` — politique unique (source de vérité)
- `core/tools/server_policy.py` — délègue (`validate_egress_url`)
- `core/llm/provider_factory.py` — délègue (`assert_literal_destination`)
- `interfaces/api/routers/{providers,config,cookbook,v1,capabilities}.py` — gates
- `tests/security/test_egress_policy.py` — blocage SSRF/métadonnées + endpoints légitimes
- `interfaces/api/tests/test_privileged_control_plane_rbac.py` — matrice gates + anti-sur-gating
- `interfaces/api/tests/test_user_management.py` — 403 admin (existant, conservé)

---

## 4. Invariants vérifiés

- **Fail-closed** : destination refusée par défaut ; la classe interdite ne
  dépend pas d'une option d'exploitation.
- **Symétrie RBAC** : aucune mutation du plan de contrôle sans permission
  dédiée ; garde automatique sur les préfixes sensibles (ajouter un préfixe à
  `PRIVILEGED_PREFIXES` suffit à protéger un nouveau domaine).
- **Non-régression inverse** : le plan de données et l'auto-administration
  (2FA) restent ouverts à tout rôle authentifié.
- **Erreur exploitable côté UI** : l'API renvoie `403` +
  `detail` explicite ; `apiFetch` le propage (`ApiError.message`) et les vues
  l'affichent, donc un refus est lisible, pas un écran vide.

---

## 5. Suite de tests : fin de la quarantaine en bloc de `tests/security`

Le dossier `tests/security` était quarantainé **en bloc** par `tests/conftest.py` :
au-delà des fichiers legacy, cela masquait aussi les tests de sécurité du code
actuel (`core.security.*`, `core.tools.*`).

- `tests/security/conftest.py` (nouveau) applique une quarantaine **locale et
  automatique** : un fichier est ignoré dès qu'il référence le paquet
  `openjarvis` supprimé au rebuild. Aucune liste de noms à maintenir, et les
  tests du code actuel sont désormais collectés par la suite globale.
- `tests/security/test_api_wiring.py` et `test_ecosystem_integration.py` :
  fabriques `_tool()` passées en `provider="custom"` — ces tests vérifient le
  câblage policy/capability (chemin simulé de l'executor), pas l'exécution d'un
  builtin natif (routé vers le Core ; seul `web_search` a un executor).

Résultat (29/09/2026) : `pytest tests/` = 1760 passed / 25 skipped / 0 erreur, et
`pytest tests/security` = 226 passed (mesure à date, durcissement des
extensions inclus — cf. `09-extension-hardening.md`). Les 21 fichiers legacy
restent à migrer via une RFC dédiée (limite pytest connue : cibler un fichier
legacy explicitement lève encore `ModuleNotFoundError: openjarvis`).

---

## 6. SecurityGateway branché sur les routes d'installation (CTO P0-1)

Le `SecurityGateway` du Core (`core/security/gateway.py`) était **inutilisable** :
`initialize()` importait `core.security.audit` (module inexistant → `ModuleNotFoundError`),
son statut de succès prétendait `"executed"` alors qu'il ne fait que **valider**,
et son rate limiting identifiait l'acteur par la *source* (« user »), donc tous
les utilisateurs partagés d'un même rôle épuisaient un compteur commun.

Réparations (dans l'ordre du flux Signatures → Permissions → Politiques → RateLimit → Audit) :

- **audit réel** : l'audit du Core (`core.audit.AuditStore`, append-only JSONL/PG)
  journalise désormais succès **et** rejets, avec `correlation_id` ;
- **statut honnête** : `"validated"` remplace `"executed"` — contrat explicite :
  *le gateway valide, le handler exécute* (séparation validation / exécution) ;
- **rate limit par acteur** : `execute(..., actor=sub)` — l'identité JWT (`sub`)
  isole chaque utilisateur ; les limites sont réglables via
  `ETHAN_GATEWAY_RATE_LIMIT` / `ETHAN_GATEWAY_RATE_WINDOW`.

Câblage interface (`interfaces/api/gateway_guard.py`, règle Première Loi :
l'interface *délègue* au Core, elle n'implémente rien) :

```
POST /v1/plugins/install ─┐
                          ├─ Depends(require_permission(PLUGINS))   ← RBAC d'abord
                          └─ Depends(gateway_guard(PLUGIN_INSTALL)) ← puis Core
POST /v1/skills/import  ──┘
```

Un rejet du gateway lève `403` (et `429` pour un dépassement de rate limit)
**avant** toute exécution ; l'ordre des dépendances est verrouillé par les tests
(un rôle non autorisé n'épuise pas le compteur du gateway). La route d'import
de skills est gardée sous la même action : importer des skills, c'est installer
du code, même si la ressource s'appelle autrement.

Contrat d'introspection : `checker.gateway_action` (comme `permission_checker.permission`)
permet aux matrices « route → garde » de relire le câblage sans exécution —
verrouillé par `interfaces/api/tests/test_security_gateway_guard_api.py`
(câblage, ordre RBAC→guard, 403/429, acteur = `sub` du JWT).

