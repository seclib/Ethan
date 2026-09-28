"use client";

/**
 * Mission → Templates — workflows pré-configurés (à venir).
 *
 * Placeholder honnête : aucun template fictif n'est affiché. Les templates
 * naîtront des workflows du Core et des capacités réellement supportées par
 * les Connections ETHAN.
 */

import { WorkspacePlaceholder } from "@/components/features/missions/workspace/workspace-placeholder";

export default function MissionTemplatesPage() {
  return (
    <WorkspacePlaceholder
      title="Templates"
      description="Des workflows pré-configurés et réutilisables, dérivés des capacités réellement supportées par ETHAN (Connections, Agents, Skills)."
      planned={[
        "Templates officielles — exemples trigger → service connecté → agent ETHAN → action(s).",
        "Validation des prérequis (Connections requises) avant instanciation.",
        "Import/export de workflows.",
        "Template store communautaire (plus tard).",
      ]}
    />
  );
}