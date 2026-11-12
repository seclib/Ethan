"use client";

/**
 * Mission → Workflows — architecture initiale de l'orchestrateur visuel.
 *
 * INSPIRATION (n8n / Zapier) : workflows = graphe de nœuds (triggers,
 * actions, conditions) branchés sur les services connectés ETHAN.
 *
 * NE PAS implémenter ici : moteur d'exécution, édition de graphe, état de
 * run. Cette page expose uniquement la ROADMAP d'architecture, honnêtement
 * marquée « à venir » — aucune donnée ni exécution fictive.
 */

import { WorkspacePlaceholder } from "@/components/features/missions/workspace/workspace-placeholder";

export default function MissionWorkflowsPage() {
  return (
    <WorkspacePlaceholder
      title="Workflows — orchestrateur visuel"
      description="Chaque workflow sera un graphe de nœuds : déclencheurs, actions, conditions et étapes, exécuté par ETHAN Core/Runtime et supervisé depuis cet espace."
      planned={[
        "Triggers — événements Core (webhook, planification, message, changement d'état).",
        "Nœuds de services connectés — GitHub, Notion, Medium, Email… via la couche Connections du Core.",
        "Nœuds ETHAN — agents, skills, knowledge, génération de contenu.",
        "Conditions et branchements entre étapes.",
        "Éditeur visuel (canvas n8n-like) — lecture d'abord, édition ensuite.",
        "Moteur d'exécution, retries et supervision dans ETHAN Runtime — jamais dans la WebUI.",
      ]}
    />
  );
}