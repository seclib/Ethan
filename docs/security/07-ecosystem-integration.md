# 07 — Intégration Écosystème (Phase 07)

> Statut : **implémenté** — Constitution, Policy Engine (04), Capability System (05)
> et Data Protection (06) branchés sur les composants réels d'ETHAN.

---

## 1. Vue d'ensemble

```
Agent / LLM ──propose──▶ Tool ──▶ SecureToolEnforcer.check ──▶ exécution
                                     │
                                     ├─ 1. PolicyEngine      (hiérarchie CORE → LLM, A1–A6)
                                     ├─ 2. CapabilityManager (sujet × ressource × opération)
                                     ├─ 3. ExfilGuard        (transmission externe, CR-4)
                                     └─ 4. AuditStore        (observabilité, append-only)
```

Invariants appliqués :
- **Loi Fondamentale** : la décision d'un LLM/agent n'est jamais une autorisation.
  L'enforcer évalue la demande, jamais le demandeur (neutralité A6).
- **Non-contournabilité** : tout tool sensible passe par `SecureToolEnforcer.check`
  ; un refus lève `ToolRejectedError` **avant** toute exécution.
- **Fail-closed** : silence policy = refus ; aucune capability = refus.

Fichiers :
- `core/security/integration.py` — `SecureToolEnforcer`, `classify_tool_call`,
  `ToolRejectedError`, `build_secure_enforcer`
- `core/tools/executor.py` — `ToolExecutor(policy_enforcer=...)`
- `core/security/status.py` — exposition de l'état sécurité
- `interfaces/api/routers/security.py` — API `/v1/security/*`
- `interfaces/webui/src/app/security/page.tsx` — page WebUI Security

---

## 2. Tools — chemin d'exécution sécurisé

`ToolExecutor` accepte un `policy_enforcer`. Si présent, chaque appel est
évalué par `classify_tool_call` (mapping **structurel** : métadonnées du tool +
paramètres — jamais le contenu d'un prompt) puis par les 4 étages.

| Étage | Rôle | Résultat en cas d'échec |
|---|---|---|
| PolicyEngine | hiérarchie, deny-by-default, confirmation | `rejected` (raison policy) |
| CapabilityManager | droit granulaire du sujet | `rejected` (`No matching active capability`) |
| ExfilGuard | transmission externe non autorisée | `rejected` (raison CR-4) |
| AuditStore | traçabilité ALLOWED/DENIED/REJECTED | — (append-only) |

Mapping des catégories (`_CATEGORY_ALIASES`) : shell/command/bash/terminal →
`shell` ; docker ; file/fs/filesystem → `filesystem` ; http/web/url/network →
`network` ; mcp ; memory ; config → `configuration` ; send/transmission/exfil →
`external_transmission` (action forcée à `send` — refusée par défaut, règle CORE
`core.net.transmission`).

**Rétro-compatibilité** : `ToolExecutor()` sans enforcer conserve le comportement
historique. La sécurité s'active explicitement via `build_secure_enforcer()`.

### Path security et catégories

Dans `Capability.matches()` :
- `filesystem` → résolution sécurisée (`resolve_safe_path`) : traversal, symlink
  escape et mount escape bloqués ; matching par préfixe (`/racine/**`).
- autres catégories (shell, docker, network, mcp…) → la ressource est une
  commande/URL : matching glob (`fnmatch`) sur la valeur brute.

---

## 3. Agent & LLM

- Un agent **propose** (tool call), **demande** (confirmation) et **agit selon
  ses capacités** (CapabilityManager par sujet `user:<id>`).
- Il ne peut pas modifier les règles supérieures : le `PolicyEngine` est
  construit hors du flux LLM ; aucune API du flux d'exécution n'expose
  `add/remove rule`. Testé : `test_docker_rejected_even_with_capability`.
- `LLM decision ≠ authorization` : la source (`context.source`) est auditée mais
  ne change jamais la décision (neutralité A6, testé).

---

## 4. Memory — hiérarchie de confiance

`core/cognition/memory/manager.py` distingue désormais les états :

```
tentative → échec → succès → résultat vérifié → procédure validée
```

- Une entrée n'acquiert le statut **connaissance fiable** qu'après validation
  explicite (`verify` / `validate`), jamais par auto-déclaration du LLM.
- Les états intermédiaires restent consultables mais ne sont pas exposés comme
  knowledge fiable au RAG/prompt.

---

## 5. Observabilité

Chaque décision est enregistrée via `_record()` → `AuditStore.log`
(catégorie `SECURITY`) :

```
actor (sujet) | category | action | resource | policy_id | decision | reason
```

Décisions auditées : `ALLOWED`, `DENIED` (policy/capability/exfil),
`REJECTED` (confirmation requise, fail-closed). Journal append-only.


---

## 6. WebUI — représentation Security

Page dédiée `/security` (hors du chat — le chat ne devient pas un panneau
d'administration) :

- **ETHAN Security** : état global (policy engine actif, exfil guard, audit)
  via `GET /v1/security/status`.
- **Capabilities** : liste des capacités actives par sujet.
- **Policies** : règles chargées (lecture seule dans l'UI).
- **Audit** : dernières décisions.

Client typé : `interfaces/webui/src/lib/api/security.ts`. L'interface n'implémente
aucune logique métier (Première Loi) : elle affiche et déclenche.

---

## 7. Tests

`tests/security/test_ecosystem_integration.py` (8 tests) :

1. `test_sensitive_tool_rejected_by_policy` — Docker refusé (SECURITY deny),
   jamais exécuté.
2. `test_shell_tool_without_capability_rejected` — policy ALLOW + zéro
   capability → refus capability.
3. `test_shell_tool_with_capability_executes` — policy ALLOW + capability →
   exécution.
4. `test_docker_rejected_even_with_capability` — la hiérarchie prime (A1/A2).
5. `test_external_transmission_tool_rejected_by_core_rule` — CR-4 : refus CORE.
6. `test_exfil_guard_rejects_without_policy` — ExfilGuard fail-closed même si
   une policy ALLOW existe (double contrôle).
7. `test_default_executor_preserves_legacy_behavior` — rétro-compat.
8. `test_classify_tool_call_maps_categories` — mapping structurel.

Validation : **78/78** tests du périmètre sécurité (phases 04–07) passent.

---

## 8. Limites connues (phases suivantes)

- `REQUIRE_CONFIRMATION` est traité fail-closed (refus) tant que le flux
  d'approbation humaine n'est pas branché sur l'exécution réelle (ApprovalEngine
  existe, exposé via `/v1/internal` uniquement).
- L'audit est en mémoire ; la persistance `AuditStore` (append-only disque)
  reste à connecter dans `build_secure_enforcer`.
- Les routes MCP/plugins ne passent pas encore toutes par l'enforcer.

