# ADR-02-F2-R — Projection contrôlée des Application Capabilities vers les agents

**Statut** : Proposition — soumise pour validation par l'owneur  
**Date** : 2026-11-05  
**État audité (2026-11-05)** : Aucune implémentation ni exécution agent par application capability n'est présente dans le code inspecté. Aucune modification de production n'a été réalisée pour cet ADR.

## 1. Contexte

ETHAN OS dispose déjà de la fondation suivante :

- `core/applications/capability_contract.py`
- `core/applications/capability_execution.py`
- `core/applications/application_registry.py`
- API `/v1/application-capabilities`
- API `/v1/applications/{application_id}/runtime`
- API d'invocation `/v1/application-capabilities/{capability_id}/invoke`

Cette fondation valide des contrats et exécute une capability par un adaptateur explicitement autorisé, avec :

- propriété applicative ;
- identifiant de capability ;
- schémas input/output JSON ;
- durées timeout ;
- validation d'entrée et de sortie ;
- allowlist d'implémentation (`odin.runtime-status`, `frame.runtime-status`) ;
- routage HROT au niveau HTTP via `Permission.EXECUTE`.

Cependant, l'« Agent Arsenal » n'est pas un composant distinct et complet dans le code inspecté. Le chemin d'exécution agent observable est :

```text
WebUI/API -> FastAPI -> _domains.agents -> AgentManager.execute() -> _executor -> runtime agent
```

`AgentManager.execute(agent_id, task, context=..., skill_id=...)` accepte un `skill_id` optionnel. Il ne dispose ni d'un `capability_id`, ni d'un contexte HROT interne, ni d'un refs d'autorisation vérifié au moment de l'invocation.

Le flux capability existant n'est donc que voisin, pas relié à `AgentManager`.

---

## 2. Sources inspectées

Code réel :

- `core/agents/manager.py`
- `core/agents/types.py`
- `core/skills/manager.py`
- `core/skills/registry.py`
- `core/skills/executor.py`
- `core/capabilities/registry.py`
- `core/applications/capability_contract.py`
- `core/applications/capability_execution.py`
- `core/applications/application_registry.py`
- `interfaces/api/main.py` (injection d'`AgentManager._executor`)
- `interfaces/api/routers/v1.py` (`execute_agent`, test de route et AgentManager, `Permission.EXECUTE`)
- `interfaces/api/routers/applications.py`
- `core/hrot/durable.py`

La HROT durable est visible comme autorité d'approbation et de consommation. L'authorization HTTP est visible comme enforcement de permission. None combined dans `AgentManager`.

---

## 3. Décision proposée

**Primaire acceptée pour discussion: Projection de capabilities vers la représentation de Skill existante, sans Skill persisté dupliqué.**

La projection doit être dérivée des sources canoniques existantes :

1. `ApplicationCapabilityContract`
2. `CapabilityExecutionBinding`
3. activation de la capability
4. implémentation allowlistée
5. snapshot runtime state / health
6. context d'exécution authentifié

L'utilisateur ne voit jamais de facette `Skill` persistante créée pour une application.

La projection agent doit conserver des états séparés :

| État | Signification |
|---|---|
| `registered` | application et contrat intégrés |
| `valid` | contrat et binding validés |
| `activated` | activation explicite |
| `authorized` | capacité HROT vérifiée au moment de l'invocation |
| `available` | runtime réutilisé et sain |
| `invoked` | adaptateur appelé |
| `failed` | erreur structurée |
| `revoked` ou `deactivated` | interdite à l'appel suivant |

### 3.1 Stratégie primaire retenue

Stratégie A — projection dérivée vers l'outil agent via le mécanisme existant.

Justification :

- L'API agent dispose déjà d'un paramètre `skill_id`.
- `SkillManager` / `SkillExecutor` / `SkillRegistry` existent comme couche technique.
- Un skill persisté ne peut pas être créé au seul motif qu'une capability applicative est déclarée, sous peine de dupliquer la source de vérité.
- `ApplicationCapabilityContract`, binding et activation restent canoniques.
- Le runtime existe déjà comme service.

### 3.2 Stratégies alternatives

**B. Adaptateur à la frontière AgentExecutor**

Avantage : point d'intégration unique.  
Risque : masque la résolution et introduit un contournement possible si le contexte authentifié n'est pas présent.  
Verdique : possible, mais seulement après contrat de contexte et HROT.

**C. Réutilisation d'un mécanisme d'outil existant**

Avantage : réutilisation maximale si le mécanisme existe et est démon>((responsabilité de `resolve_agent_resources`, qui résoud `agent.tool_ids`).

Risque : le trait `AgentManager.execute()` observe uniquement `_executor`, sans preuve dans ce dépôt que le mécanisme `ToolManager` soit réellement invoqué par cette voie.

Verdict : `NOT VERIFIED` dans ce dépôt pour cette campagne.

---

## 4. Contexte d'exécution authentifié

Il faut introduire un **contexte d'exécution de trusted agent**, distinct de :

- l'identité HTTP de la route ;
- des données de `task` ;
- des données arbitraires de `context`.

Ce contexte doit être construit côté serveur à partir de l'identité authentifiée et propagé sans possibilité de contournement.

Proposition minimale :

```python
@dataclass(frozen=True)
class AgentExecutionContext:
    execution_id: str
    agent_id: str
    principal_id: str | None
    role: str | None
    correlation_id: str
    started_at: datetime
    source: str  # route_http, autonomy, scheduler, ...
```

Règles :

1. L'identité provient d'une source server-side, jamais de `task` ni de `context`.
2. La route agent peut créer le contexte depuis un JWT et HROT disponibles.
3. `AgentManager.execute(..., context=...)` doit recevoir ce contexte en argument contrôlé.
4. Si le demandeur est absent et que le mode de lifecycle l'exige, l'invocation capability est refusée.
5. Le contexte doit être stocké et tracé, non salvable par l'utilisateur.

## 5. HROT et autorisation interne

### 5.1 Observations

- `interfaces/api/routers/v1.py::execute_agent` applique `require_permission(Permission.AGENTS)`.
- `_ensure_agent_access` vérifie ownership et rôle.
- `core/hrot/durable.py` expose des approvals persistantes.
- `core/auth/__init__.py::rbac` expose `has_permission`.
- `ProviderGateway` isole les secrets.

### 5.2 Règle proposée

L'authorization doit se faire à deux niveaux:

1. **Au niveau API** : valider l'identité humaine et le rôle.
2. **Au niveau runtime agent** : associer cette identité applicative au `binding` et au contrat, et relancer une décision HROT par pair `(application_id, capability_id, binding_id, principal_id, scope)`.

Si l'HROT actuel ne permet ni d'enregistrer ni de relancer une décision dans ce chemin, cela doit être signalé comme lacune HROT, pas contourné par une condition locale.

La stratégie A propose de passer le contexte authentifié aux primitives existantes.

### 5.3 Limite actuelle

Le code actuel ne possède pas, dans `AgentManager`, de champ pour la décision HROT.

Il faut ajouter le minimum, par exemple :

- `AgentExecution.identity_context: dict` ou un champ typé non-inventé (`execution_context`).
- un champ `authorization_reference` si nécessaire.

Je refuse de recoder une autorité parallèle.

## 6. Modèle de projection minimale

Proposition de mapping dérivé:

```text
application_id:capability_id
```

Résolution déterministe :

1. récupérer `ApplicationCapabilityContract`
2. récupérer `CapabilityExecutionBinding`
3. vérifier la version du binding
4. vérifier `binding.activated`
5. résoudre l'implémentation allowlistée
6. valider `input_schema`
7. invoquer l'adaptateur
8. valider `output_schema`
9. persister le statut et la décision HROT
10. retourner au agent

### 6.1 États séparés

- `registered` : contrat associé
- `valid` : vérifications contractuelles
- `bound` : binding établi
- `activated` : explicitement activé
- `available` : runtime réutilisé et inspecté
- `authorized` : décision HROT valide
- `invoked` : exécution a été faite
- `completed` ou `failed` : résultat
- `revoked` : autorisation rétroactivement refusée

Ces états ne doivent pas être conflue.

## 7. HROT et permissions

Autorité :

- `core/hrot/durable.py::HrotDurableAuthorizationAuthority`
- `Permission` RBAC
- `require_permission`

Condition proposée :

- API Hz permission `Permission.EXECUTE` et ownership.
- Capability contract `required_permissions`.
- Binding dément le couple capability/implementation.
- HROT durable refuse, expire, révoque.
- Implementation allowlist contrainte.

Le minimum acceptable est une décision opaque avec corrélation, pas une hypothèse.

### Audit Trail minimal

`AgentExecution` et `CapabilityExecution` devraient contenir, si une implémentation de cette proposition est jamais initiée :

- `execution_id`
- `agent_id`
- `principal_id`
- `correlation_id`
- `application_id`
- `capability_id`
- `binding_id`
- `authorization_reference`
- timestamps
- status
- errors only sanitized

## 8. Sécurité et boundary

Les règles proposées :

- ne jamais exécuter un module, chemin ou commande fourni par l'agent ;
- ne jamais transformer un `capability` en commande directe `shell` ;
- ne jamais exposer les secrets ;
- ne pas traverser un dépôt oulynx ;
- entrée/sortie JSON Schema strict ;
- timeout bounded ;
- implémentation par allowlist nommée ;
- échec et erreur structurés, jamais fuite ;
- activation explicit, retrait explicit ;
- HROT authorization required at invocation.

## 9. Conditions non implémentées aujourd'hui

- Pas de contexte d'acteur au niveau `AgentManager.execute`.
- Pas de résolution de capacité côté agent.
- Pas d'autorisation HROT interne dans ce chemin.
- Pas de projection d'outil applicatif actuellement démontrée.
- Pas de parcours agent réel validé.

Ces absences ne sont pas des preuves de `PARTIAL` ou `RUNTIME_VALIDATED` et ne justifient pas une déclaration d'implémentation.

## 10. Alternatives

A — Projection Skill (`préférée conceptuellement`)  
- Avantage : réutilise `skill_id`, `SkillManager` et `SkillExecutor`.
- Inconvénient : collision sémantique si la projection s'auto-persiste.
- Conclusion : faire dériver, pas dupliquer.

B — Adaptateur frontière AgentExecutor  
- Avantage : point d'intégration clair.
- Inconvénient : masquage et risque si l'exécuteur injecté n'est pas inspecté.
- Conclusion : accepté si et seulement si les primitives HROT et facteur contexte sont fournis.

C — Réutilisation directe tool existant  
- Avantage : maximiser la réutilisation.
- Inconvénient : aucune route observable pour le faire.
- Conclusion : `NOT VERIFIED`.

## 11. Décision soumise à l'owneur

### ADR proposée, pas acceptée

Adopter la stratégie A — Skill-aware projection — comme choix d'architecture, avec une condition de sécurité :

1. HROT provide internal authorization primitives and identity propagation before production.
2. Application capabilities remain the canonical source of truth.
3. Capability binding remains the mapping and is activated only through approval.
4. Invocation stays allowlisted and schema-validated.
5. AgentManager receive authenticated execution context, via a minimal extension.
6. Execution evidence includes authorization scope.

### Obligation

Ne pas déclarer implémenté avant démonstration. Les tests unitaires ne constitueront pas une preuve à eux seuls.

## 12. Status

- Architecture Investigation: `COMPLETED`
- Integration Strategy: `SELECTED` (A)
- Proposed Model of execution context: `IMPLEMENTED` (as documentation), `NOT VERIFIED` in code
- Agent identity propagation: `NOT VERIFIED`
- HROT internal authorization: `NOT_VERIFIED`
- Capability projection feasibility: `PARTIAL`
- Production changes: `NONE`
- Runtime agent invocation: `NOT_IMPLEMENTED`
- Quantar : `PAUSED` / `BLOCKED`
- Browser E2E : `NOT_VALIDATED`

## 13. Fichiers concernés (lecture seulement)

- `core/agents/manager.py`
- `core/skills/manager.py`
- `core/skills/registry.py`
- `core/skills/executor.py`
- `core/capabilities/registry.py`
- `core/applications/capability_contract.py`
- `core/applications/capability_execution.py`
- `core/applications/application_registry.py`
- `core/auth/__init__.py`
- `core/hrot/durable.py`
- `core/security/hrot_provider_gateway.py`
- `interfaces/api/routers/v1.py`
- `interfaces/api/routers/applications.py`
- `interfaces/api/main.py`

## 14. Validation sans exécution

Cette passe est document-only. Aucun test de production supplémentaire n'a été exécuté et aucun code n'a été modifié.

Alternatives, status and security requirements are recorded.

Aucun secret n'a été exposé. Quantar reste en pause.
