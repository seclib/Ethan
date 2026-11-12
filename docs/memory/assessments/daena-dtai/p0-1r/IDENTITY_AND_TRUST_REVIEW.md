# IDENTITY_AND_TRUST_REVIEW.md

Audit C — Chaîne d'identité et de confiance : `Authenticated Principal → ExecutionContext → Agent Identity → Capability Invocation → HROT Decision`.

Mission P0-1R — Indépendant, lecture seule.

---

## 1. Chaîne d'identité complète

### 1.1 Authentification middleware (`interfaces/api/auth.py`)

L'authentification est gérée par `auth_middleware` (ligne 250-389). Elle traite trois chemins :

| Chemin | Condition | Identité résultante |
|--------|-----------|---------------------|
| Service identity JWT | Cookie/Bearer avec `typ=service` ou `iss=ethan.service` | `AgentPrincipal` type `SERVICE`, signé via `issue_trusted_principal()` |
| API Key | Header `X-API-Key` ou cookie `ethan_*` | `AgentPrincipal` type `API_KEY`, signé |
| JWT utilisateur (humain) | Cookie `ethan_token` ou Bearer JWT | `AgentPrincipal` type `HUMAN`, signé, après validation du compte utilisateur via `fetch_user_record()` |

Le middleware peuple `request.state` :
- `request.state.user` : identifiant (sub)
- `request.state.token_payload` : payload JWT brut
- `request.state.principal` : `AgentPrincipal` signé (via `build_agent_principal()`)
- `request.state.request_id` : ID de requête

### 1.2 `build_agent_principal()` (ligne 401-590)

Construit un `AgentPrincipal` signé (HMAC-SHA256 avec `JWT_SECRET`). Vérifications effectuées :
- Pour HUMAN : le compte utilisateur doit exister (`fetch_user_record`), être actif (`is_active`), avoir un rôle. Le principal ne peut pas être construit à partir du seul claim JWT sans compte persistant (fail-closed, ligne 553-567).
- Pour API Key : la clé doit être active.
- Pour Service : le service doit être enregistré et validé.

### 1.3 `ExecutionContext` (`core/auth/principal.py` ligne 223-287)

Dataclass gelée contenant :
- `principal: AgentPrincipal` (obligatoire)
- `agent_id: str | None`
- `service_id: str | None`
- `request_id: str | None`
- `delegated_permissions: tuple[str, ...]` (doit être un sous-ensemble des permissions du principal — vérifié à la construction, ligne 242-243)

### 1.4 Construction dans la route API (`applications.py` ligne 316-333)

```python
principal = getattr(request.state, "principal", None)
execution_context = None
if principal is not None:
    execution_context = ExecutionContext(
        principal=principal,
        agent_id=principal.actor_id or principal.subject_id,
        request_id=principal.request_id,
    )
```

**Point critique :** si `request.state.principal` est None (par exemple si le middleware n'a pas été appliqué, ou si l'appel provient d'un contexte interne non-HTTP), alors `execution_context = None` → transmis à `invoke_capability()` → HROT étape 1 → DENY `MISSING_EXECUTION_CONTEXT`. **Fail-closed correct.**

### 1.5 Transmission à `invoke_capability()` (`capability_execution.py` ligne 199-215)

```python
agent_id = ""
if execution_context is not None:
    agent_id = getattr(execution_context, "agent_id", None) or ""
hrot_request = CapabilityAuthorizationRequest(
    execution_context=execution_context,
    agent_id=agent_id,
    ...
)
```

L'`agent_id` passé à HROT provient de `execution_context.agent_id`, qui provient de `principal.actor_id or principal.subject_id`.

---

## 2. Vérification des propriétés de confiance

| Propriété | Statut | Preuve |
|-----------|--------|--------|
| L'identité provient d'un middleware d'authentification de confiance | CONFIRMÉ | `auth_middleware()` (auth.py:250-389) vérifie JWT/API Key/Service avant de peupler `request.state.principal` |
| L'agent est lié à un contexte d'exécution authentifié | CONFIRMÉ | `ExecutionContext.principal` est un `AgentPrincipal` signé (HMAC) |
| L'agent ne peut pas sélectionner un autre acteur | PARTIEL | Le `request.agent_id` dans `CapabilityAuthorizationRequest` est passé par l'appelant. L'étape 3 vérifie `context.agent_id == request.agent_id`, mais si l'appelant interne contrôle les deux, il peut les faire correspondre avec une identité forgée. |
| Les permissions ne peuvent pas être injectées par des données de requête non fiables | CONFIRMÉ (RBAC) | Les permissions proviennent de `context.principal.permissions` (signé), pas du `request` directement. Cependant, voir faiblesse HROT-02 (pas de `verify_trusted_principal`). |
| Les identifiants de requête sont propagés | CONFIRMÉ | `request_id` est propagé du middleware vers `ExecutionContext` puis vers `CapabilityAuthorizationRequest.correlation_id` et `execution_id` |
| Les incompatibilités d'identité causent un refus explicite | CONFIRMÉ | Étape 3 `AGENT_IDENTITY_MISMATCH` → DENY |

---

## 3. Faiblesse HROT-02 (détaillée) — Pas de vérification cryptographique du principal

Dans `CapabilityAuthorizationService._evaluate()` (ligne 304) :

```python
context = _coerce_execution_context(request.execution_context)
if context is None:
    return self._record(_deny("MISSING_EXECUTION_CONTEXT", ...))
```

La fonction `_coerce_execution_context` (ligne 31-48) accepte :
1. Un objet possédant `principal` et `to_dict` → accepté tel quel
2. Un `Mapping` → tente `ExecutionContext.from_dict()` (désérialise un `AgentPrincipal` depuis un dict, **sans vérification de signature HMAC**)

**Aucun appel à `verify_trusted_principal()` n'est effectué dans `_evaluate()`.** Cela signifie :

- Un appelant interne ayant accès au code peut construire un `AgentPrincipal` avec n'importe quelles `permissions`, `actor_id`, `subject_id`, et l'envelopper dans un `ExecutionContext`, puis l'injecter via `invoke_capability(..., execution_context=forged_context)`.
- L'étape 3 vérifie que `context.agent_id == request.agent_id`, mais l'appelant contrôle les deux.
- L'étape 8 vérifie `principal.has_permission(permission)`, mais si le principal est forgé avec toutes les permissions, cette vérification est contournée.

**Cette faiblesse n'est exploitable que par un appelant interne ayant déjà accès au code Python de `invoke_capability()` ou de `CapabilityAuthorizationService.authorize()`.** Elle n'est pas exploitable via l'API HTTP publique, car le middleware d'authentification construit et signe le principal avant que la route ne soit appelée.

---

## 4. Chaîne d'identité — Diagramme

```
Utilisateur/Agent
     │
     ▼
[Middleware auth] ──► JWT vérifié ──► build_agent_principal() ──► AgentPrincipal signé (HMAC)
     │                                                │
     │                                                ▼
     │                                        request.state.principal
     │                                                │
     │                                                ▼
     │                               [Route API invoke_application_capability]
     │                                                │
     │                                                ▼
     │                               ExecutionContext(principal=..., agent_id=..., request_id=...)
     │                                                │
     │                                                ▼
     │                               [invoke_capability(..., execution_context=...)]
     │                                                │
     │                                                ▼
     │                               CapabilityAuthorizationRequest(..., agent_id, ...)
     │                                                │
     │                                                ▼
     │                               CapabilityAuthorizationService._evaluate()
     │                           ├─ Étape 1: contexte présent ?
     │                           ├─ Étape 2: acteur présent ?
     │                           ├─ Étape 3: agent_id correspond ?
     │                           ├─ Étape 4-7: app/cap/binding valides ?
     │                           ├─ Étape 8: principal.has_permission() ?
     │                           └─ Étape 8/9: permission_service.authorize() ?
     │                                                │
     │                                                ▼
     │                               ALLOW / DENY (enregistré dans _decisions)
     │                                                │
     │                                                ▼
     │                         [invoke_capability] ──► implémentation (Odin/Frame) OU refus
```

---

## 5. Conclusion

La chaîne d'identité est **cryptographiquement signée du côté du middleware HTTP** (HMAC-SHA256 sur `AgentPrincipal`), ce qui empêche la falsification depuis l'extérieur. Cependant :

1. **Pas de re-vérification côté service HROT** : `verify_trusted_principal()` n'est jamais appelé dans `CapabilityAuthorizationService._evaluate()`. Un appelant interne peut injecter un `AgentPrincipal` forgé.
2. **L'agent_id est sous le contrôle de l'appelant** dans `CapabilityAuthorizationRequest.agent_id`, bien que l'étape 3 le compare à `context.agent_id`. Si les deux sont forgés de manière cohérente, l'étape 3 est contournée.

Ces faiblesses sont **limitées aux appelants internes** (code Python ayant accès à `invoke_capability` ou `authorize()`). Elles ne sont pas exploitable via l'API HTTP publique.
