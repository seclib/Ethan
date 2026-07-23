# API Clients — Guide d'utilisation

## Résumé

Deux clients API coexistent dans le projet. Ils ont des objectifs différents.

| | `src/lib/api-client.ts` | `src/core/api/api-client.ts` |
|---|---|---|
| **Rôle** | Client HTTP simple, générique | Client HTTP avec intercepteurs, services métier |
| **Auth** | Aucune | Bearer token via `localStorage` |
| **Structure** | Fonctions utilitaires (`getHealth`, `sendMessage`, etc.) | Classes `ApiClient` + services (`authService`, `agentsService`, etc.) |
| **Cas d'usage** | Healthchecks, monitoring, outils bas-niveau | Fonctionnalités métier (agents, goals, memory, skills, flux, settings) |
| **Maintenance** | Stable, peu de changes | Évolutif, ajout de endpoints métier |

## Quand utiliser quoi ?

- Utiliser `src/core/api/api-client.ts` pour toute fonctionnalité métier nécessitant une authentification ou des services réutilisables.
- Utiliser `src/lib/api-client.ts` pour les appels system indépendants (healthchecks, metrics, diagnostics).

## Dette technique

La duplication est mineure mais documentée. Si la simplification est nécessaire, prioriser le client `core/api` et déprécier doucement `lib/api-client`.

## Exemple d'usage
 
```typescript
// Client simple (lib)
import { apiClient } from "@/lib/api-client";
const health = await apiClient.getHealth();

// Client métier (core)
import { agentsService } from "@/core/api/api-client";
const agents = await agentsService.getAll();