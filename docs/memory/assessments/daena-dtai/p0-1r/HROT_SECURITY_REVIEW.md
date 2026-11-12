# HROT_SECURITY_REVIEW.md

Audit de la limite d'autorisation (Audit B) — `CapabilityAuthorizationService.authorize()` dans `core/hrot/capability_authorization.py`.

Mission P0-1R — Indépendant, lecture seule. Aucune modification de code.

---

## 1. Vue d'ensemble

La classe `CapabilityAuthorizationService` (lignes 190-599) implémente l'évaluation d'autorisation HROT pour les invocations de capacité applicative d'agents. Elle déclare explicitement ne **pas invoquer d'implémentation de capacité** ; elle évalue et enregistre seulement une décision d'audit.

L'évaluation suit **10 étapes séquentielles**, toutes en mode fail-closed (toute exception → DENY).

---

## 2. Analyse étape par étape

### Étape 1 — Contexte d'exécution de confiance (ligne 304-310)

```python
context = _coerce_execution_context(request.execution_context)
if context is None:
    return self._record(_deny("MISSING_EXECUTION_CONTEXT", ...))
```

- **Ce qui est vérifié :** `request.execution_context` doit être coercible en `ExecutionContext` (possède `principal` et `to_dict`, ou est un Mapping convertible).
- **Origine des données :** fourni par l'appelant (`invoke_capability` reçoit `execution_context` de la route API, qui le construit depuis `request.state.principal`).
- **Peut-il être omis ?** Oui — `execution_context` a une valeur par défaut `None` dans `invoke_capability()`. Si omis, étape 1 → DENY. **Fail-closed correct.**
- **Peut-il être modifié par l'appelant ?** Oui, l'appelant passe directement l'objet. Cependant, `_coerce_execution_context` ne vérifie pas la signature cryptographique du principal (voir Audit C). Un appelant interne malveillant pourrait construire un `ExecutionContext` avec un `AgentPrincipal` forgé.
- **Échec :** DENY `MISSING_EXECUTION_CONTEXT`.

### Étape 2 — Identité acteur (ligne 313-320)

```python
actor = _actor_id(context)
if actor is None:
    return self._record(_deny("MISSING_ACTOR_IDENTITY", ...))
```

- **Ce qui est vérifié :** `context.principal.actor_id` (ou `subject_id` / `principal_id`) doit être une chaîne non vide.
- **Origine :** `AgentPrincipal.actor_id`, peuplé par `build_agent_principal()` dans `interfaces/api/auth.py`.
- **Peut-il être omis ?** Oui → DENY.
- **Échec :** DENY `MISSING_ACTOR_IDENTITY`.

### Étape 3 — Identité agent (ligne 323-340)

```python
context_agent = getattr(context, "agent_id", None)
if str(context_agent).strip() != str(request.agent_id).strip():
    return self._record(_deny("AGENT_IDENTITY_MISMATCH", ...))
```

- **Ce qui est vérifié :** l'agent_id du contexte doit correspondre exactement à `request.agent_id`.
- **Origine :** `ExecutionContext.agent_id` (rempli par la route API depuis `principal.actor_id or principal.subject_id`) vs `request.agent_id` (rempli par `invoke_capability` depuis l'argument).
- **Peut-il être contourné ?** Un appelant interne pourrait passer `request.agent_id` égal à `context.agent_id` avec un agent_id forgé. Le contexte lui-même n'est pas signé (pas d'appel à `verify_trusted_principal` dans `_evaluate`).
- **Échec :** DENY `AGENT_IDENTITY_MISMATCH`.

### Étape 4 — Application enregistrée (ligne 343-352)

```python
application = self.resolve_application(registry, request.application_id)
if application is None:
    return self._record(_deny("UNKNOWN_APPLICATION", ...))
```

- **Ce qui est vérifié :** l'application doit exister dans le registre (`registry.get(app_id)` ou `registry.list()`).
- **Origine :** `request.application_id`.
- **Échec :** DENY `UNKNOWN_APPLICATION`.

### Étape 5 — Capacité enregistrée (ligne 355-365)

```python
registration = self.resolve_registration(registry, request.application_id, request.capability_id)
contract = self.resolve_contract(registry, request.application_id, request.capability_id)
if registration is None or contract is None:
    return self._record(_deny("UNKNOWN_CAPABILITY", ...))
```

- **Ce qui est vérifié :** la capacité doit être enregistrée pour cette application avec un contrat.
- **Échec :** DENY `UNKNOWN_CAPABILITY`.

### Étape 6/7 — Registration active et binding (ligne 368-449)

- **Registration :** `registration.registration_state == "registered"` et `registration.approved is True`.
- **Binding :** `resolve_binding()` doit retourner un binding non None, activé (`activated is True`), avec `contract_version` correspondant, et `application_id`/`capability_id` correspondants.
- **Anti-contournement binding (lignes 390-409) :** le `binding` ou `binding_id` fourni par l'appelant est comparé au binding canonique du registre. S'ils diffèrent → DENY `BINDING_MISMATCH`. **BON :** l'appelant ne peut pas injecter un binding forgé.
- **Échec :** DENY `INACTIVE_CAPABILITY`, `MISSING_BINDING`, `INACTIVE_BINDING`, `BINDING_CONTRACT_VERSION_MISMATCH`, `BINDING_SCOPE_MISMATCH`.

### Étape 8 — Permissions acteur (RBAC) (ligne 451-469)

```python
principal = getattr(context, "principal", None)
required_permissions = getattr(contract, "required_permissions", ()) or ()
for permission in required_permissions:
    has = False
    if principal is not None and hasattr(principal, "has_permission"):
        has = bool(principal.has_permission(permission))
    if not has:
        return self._record(_deny("MISSING_REQUIRED_PERMISSION", ...))
```

- **Ce qui est vérifié :** le principal doit posséder chaque permission requise par le contrat (`contract.required_permissions`).
- **Origine :** `context.principal` (AgentPrincipal depuis le contexte).
- **Peut-il être contourné ?** Si `principal` est None (contexte sans principal), `has` reste False → DENY. Si le principal est forgé (appelant interne), il pourrait avoir n'importe quelles permissions. Voir Audit C.
- **Échec :** DENY `MISSING_REQUIRED_PERMISSION`.

### Étape 8/9 — Policy HROT (ligne 471-512)

```python
permission_service = self._permission_service_for(request)
...
if permission_service is not None and hasattr(permission_service, "authorize"):
    result = permission_service.authorize(...)
    allowed = bool(getattr(result, "allowed", False)) or ...
    if not allowed:
        return self._record(_deny(reason, ...))
```

- **Ce qui est vérifié :** `PermissionService.authorize()` évalue les grants explicites (scope app_id/instance_id/capability/resource/action).
- **FAIBLESSE IDENTIFIÉE :** si `permission_service` est None (ligne 476 `if permission_service is not None`), l'étape entière est **sautée**. Aucun grant n'est vérifié. L'autorisation repose alors uniquement sur les étapes 1-7 (contexte, identité, registration, binding, RBAC principal).
- **Origine du permission_service :** `request.permission_service` ou `self.permission_service` (défini dans `__init__`, ligne 205-211 : tente d'instancier `PermissionService(production_mode=False)`).
- **Dans `invoke_capability()` :** le `permission_service` du registre est passé (ligne 194-197, 214). Dans `authorize_agent_capability()` (fonction de convenance, ligne 570-580), le `permission_service` vient de `kwargs` (peut être None).
- **Échec :** DENY `HROT_PERMISSION_DENIED` ou `AUTHORIZATION_EVALUATION_ERROR`.

### Étape 10 — Allow (ligne 514-539)

Si toutes les étapes précédentes passent, une décision ALLOW est enregistrée.

---

## 3. Gestion des exceptions

### Bloc try/except global (ligne 299, 540-556)

```python
try:
    ... tout _evaluate ...
except Exception as exc:
    logger.exception("Agent capability authorization failed closed: %s", exc)
    return self._record(_deny("AUTHORIZATION_EVALUATION_ERROR", ...))
```

- **Comportement :** toute exception non attrapée à l'intérieur entraîne un DENY. **Fail-closed correct.**
- **Exception dans `_deny` lui-même :** capturée par le bloc extérieur (ligne 540-556) qui appelle `_deny` avec `request=request` (peut être None si l'exception survient avant la construction de la requête... mais `request` est toujours défini à ce point car `_evaluate` reçoit `request` en argument).
- **Exception dans `_record` (ligne 558-563) :** silencieusement ignorée (`try/except: pass`). La décision n'est pas enregistrée dans `_decisions` mais est retournée. L'audit en mémoire est donc potentiellement incomplet en cas d'échec d'enregistrement.

---

## 4. Points faibles identifiés

| # | Point faible | Sévérité | Preuve (fichier:ligne) |
|---|-------------|----------|------------------------|
| HROT-01 | `permission_service` peut être None → étape HROT policy (grant) sautée | HIGH | `capability_authorization.py:476` |
| HROT-02 | Aucun appel à `verify_trusted_principal()` dans `_evaluate()` → un `AgentPrincipal` forgé par un appelant interne est accepté | HIGH | `capability_authorization.py:304` (pas de vérification de signature) |
| HROT-03 | `enforce_hrot: bool = True` paramètre contournable par un appelant interne | MEDIUM | `capability_execution.py:161` |
| HROT-04 | `execution_context` peut être None → refusé (fail-closed correct, mais appelant interne peut passer un contexte forgé) | MEDIUM | `capability_execution.py:162` |
| HROT-05 | Échec de `_record()` silencieusement ignoré → décision d'autorisation non tracée en mémoire | MEDIUM | `capability_authorization.py:558-563` |
| HROT-06 | Code mort (lignes 272-299 dupliquant 243-270) — pas de faille sécurité mais défaut de qualité | LOW | `capability_execution.py:272-299` |

---

## 5. Conclusion de l'audit B

Le mécanisme HROT `CapabilityAuthorizationService.authorize()` est **structuralement solide** (10 étapes, fail-closed, anti-contournement binding, audit en mémoire). Cependant :

1. **L'étape HROT policy (grant) est conditionnée à la présence d'un `permission_service`.** Si aucun service de permissions n'est injecté, l'étape est sautée et l'autorisation repose uniquement sur le RBAC du principal (étape 8), qui vérifie les permissions du token JWT mais pas les grants HROT explicites (approbation humaine, manifest fingerprint, etc.).

2. **Aucune vérification cryptographique du principal** (`verify_trusted_principal` n'est pas appelé dans `_evaluate`). Un appelant interne disposant d'un accès au code pourrait construire un `AgentPrincipal` avec des permissions arbitraires et l'injecter dans l'`ExecutionContext`.

3. **Le paramètre `enforce_hrot` peut être désactivé par un appelant interne** de `invoke_capability()`, bien que la route API ne le fasse pas.

Ces points doivent être corrigés avant que P0-1 puisse être considéré comme totalement sécurisé.
