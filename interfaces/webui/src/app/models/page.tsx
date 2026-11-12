"use client";

/**
 * Models page — point d'entrée du Model Hub ETHAN.
 *
 * Le composant ModelHub contient les trois onglets (Installed / Discover / Downloads)
 * et délègue toute logique métier au Core via l'API.
 *
 * L'ancien ModelsWorkspace (catalogue discovered + custom) reste accessible en
 * import direct si nécessaire, mais cette page utilise désormais le hub unifié.
 */

import { ModelHub } from "@/components/features/models/components/model-hub";

export default function ModelsPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col px-4 py-3">
      <ModelHub />
    </div>
  );
}
