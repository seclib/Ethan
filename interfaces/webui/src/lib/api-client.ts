/**
 * ETHAN API Client — re-export canonique
 *
 * L'implémentation unique est dans @/core/api/api-client.ts
 * Ce fichier est conservé pour la rétrocompatibilité uniquement.
 *
 * @deprecated Importer directement depuis "@/core/api/api-client"
 */
export {
  apiClient,
  authService,
  agentsService,
  goalsService,
  memoryService,
  skillsService,
  fluxService,
  settingsService,
} from "@/core/api/api-client";

export type { HealthStatus, SystemMetrics } from "@/core/api/types";
