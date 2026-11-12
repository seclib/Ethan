# Spécification — Préparation à l'intégration applicative (MEM-014 Phase 13)

## Registre

`ApplicationIntegrationRegistry` réutilise :

- `ApplicationManifest`
- `ExtensionContract`
- `ComplianceEngine`
- `PermissionService`
- `ApplicationLifecycleManager`
- `EventCollector`
- `ApplicationStateStore`

## Contrat

Identité, capacités, dépendances, permissions demandées, conformité, lifecycle et événements sont suivis séparément des autorisations.

## Garanties

- Aucune permission automatique.
- Application disponible sans privilège d'exécution.
- Refus par défaut via le PermissionService.
- Persistance du registre.

## Limites

- Pas d'adaptateur réel pour Odin, Frame ou TradingAgents.
- Pas de flux distant ni de nouvelle interface Web.

## Campaign 01-D / 01-D2 — registration approuvée

Ajouts :
- `ApplicationRegistrationService` enregistre uniquement après approbation HROT exacte.
- Liaison : application ID, repository identity, fingerprint manifest, preview, mandated operation.
- L'approbation HROT est consommée avant l'écriture registry.
- La dérive du principal authentifié depuis un simple paramètre appelant est éliminée par rejet strict en présence d'identité incompatible.
- Persistance partagée par SQLite avec relecture de store et lock local.
- Non-atomicité entre HROT consumption et registry persistence documentée.

## Campaign 01-D / 01-D2 — trusted actor tightening

- Authenticated principal is now accepted and must match HROT approval requester.
- Untrusted or contradictory `security_context` is rejected.
- Registry save now fails loudly instead of being swallowed.
- Registry reads are refreshed from the durable store before duplicate detection.
- Cross-process transactional atomicity remains documented as partial.

## Campaign 01-D / 01-D3 — trust boundary closure

- Suite dédiée : `tests/core/test_campaign_01_d3_trust_boundary.py` (6 tests).
- Principal authentifié requis sans preuve d'authentification librement acceptée.
- Injection trusted_actor/principal_id/security_context rejetée.
- Rejeu d'approbation bloqué par déjà_registered.
- Non-atomique register/consume reste documentée.

## Campaign 01-D / 01-D5 — durability hardening

- `asyncio.Lock` par instance est complété par un verrou de fichier sur le store lorsque présent.
- La sauvegarde registry reste fail-closed (RuntimeError).
- La preuve d'authentification reste structurelle et doit provenir de la chaîne API canonical.
- L'atomicité cross-store n'est pas revendiquée; état consommé sans registration reste récupérable uniquement par nouvelle approbation exacte.

## DTAI-02 — Generic discovery

- `LocalRepositoryDiscovery.discover()` can now discover a repository supplied as the configured root itself, in addition to nested repositories.
- This improves generic discovery of `~/AI/TradingAgents` without modifying its contents.
- Automatic preview remains `absent` for candidate repositories lacking an ETHAN manifest.

## DTAI-02D — Generic Tools catalog UI

- `ApplicationCatalog` now renders generic catalog metadata from `GET /v1/application-integration/catalog`.
- Integrated as an "Applications" tab in `ToolsHub`.
- Preserves existing Tools and MCP tabs.
- Odin, Frames and Hyperframes are not modified.
- No application-specific React component or route was introduced.
- TypeScript typecheck passed for the WebUI changes.

## DTAI-02E — Multi-source generic catalog

- `IntegrationCatalogService.build` supports multiple configurable roots.
- Roots are resolved from `ETHAN_LOCAL_REPOSITORY_ROOTS`, then legacy `ETHAN_LOCAL_REPOSITORY_ROOT`, with deterministic de-duplication.
- Source provenance is returned per repository.
- Missing roots are partial source errors, not fatal.
- ComfyUI and an external repository root such as `~/AI/TradingAgents` can both appear without app-specific code.
- API uses the existing catalog route.
- WebUI adds a generic `Applications` tab using `ApplicationCatalog`.

## DTAI-03E — Persistent manifest repository

- `ApplicationManifestRepository` stores application manifests in the canonical ApplicationStateStore.
- Schema v5 adds `application_manifests`.
- Supports create, list, get_current, update with incremental `record_version`, provenance and validation state.
- Does not register, install, start or execute applications.
- ComfyUI manifest can be persisted and reloaded without modifying its repository.
- API `application_manifests` read endpoint added.
