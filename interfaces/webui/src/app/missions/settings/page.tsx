"use client";

/**
 * Mission → Settings — préférences du workspace (à venir).
 *
 * Placeholder honnête : les préférences (notifications d'exécution,
 * concurrence, rétention des runs…) nécessiteront une configuration dans
 * ETHAN Core. Aucun contrôle factice n'est rendu.
 */

import { WorkspacePlaceholder } from "@/components/features/missions/workspace/workspace-placeholder";

export default function MissionSettingsPage() {
  return (
    <WorkspacePlaceholder
      title="Settings du workspace Mission"
      description="Préférences du workspace : notifications d'exécution, concurrence des workflows, rétention de l'historique des runs."
      planned={[
        "Notifications d'exécution (échec, succès, validation requise).",
        "Limites d'exécution (concurrence, timeout par étape).",
        "Rétention et purge de l'historique des runs.",
        "Sources de vérité : configuration Core (ConfigurationService) — la WebUI ne fait qu'afficher et modifier via l'API.",
      ]}
    />
  );
}