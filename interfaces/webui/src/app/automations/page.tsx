"use client";

/**
 * Page Automations — règles persistées par ETHAN Core
 * (AutomationManager, core/scheduler/automations.py ; /v1/automations).
 *
 * Interface = présentation seule : lister, créer, activer/désactiver,
 * déclencher et supprimer. Déclencher émet l'événement `automation.triggered`
 * sur le bus ; l'exécution des actions appartient au Runtime.
 */

import { AutomationsWorkspace } from "@/components/features/automations/automations-workspace";

export default function AutomationsPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <AutomationsWorkspace />
    </div>
  );
}
