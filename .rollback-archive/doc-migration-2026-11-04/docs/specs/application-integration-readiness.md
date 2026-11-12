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
