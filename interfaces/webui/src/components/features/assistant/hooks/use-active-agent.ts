"use client";

/**
 * ETHAN WebUI — Sélection de l'agent actif (symétrique de use-active-model).
 *
 * Source de vérité : ETHAN Core via GET /v1/agents (hook useAgents — cache
 * React Query partagé avec la page /agents : toute mutation côté Core ou
 * workspace invalide ce catalogue automatiquement).
 *
 * Responsabilités (front uniquement) : récupérer · afficher · sélectionner.
 * Aucune logique métier d'agent ici — la résolution effective
 * (instructions, provider/model par défaut, fusion skills/knowledge/tools)
 * reste implémentée dans core/chat/pipeline.py ; le payload chat porte
 * simplement `agent_id`.
 */

import { useCallback, useEffect, useRef } from "react";
import { useAgents } from "@/components/features/agents/hooks/use-agents";
import { useUIStore } from "@/store/ui.store";
import { useAgentStore } from "@/store/agent.store";
import type { Agent } from "@/types";

const MAX_RECENT = 3;

export function useActiveAgent() {
  const { agents, isLoading, error } = useAgents();
  const addToast = useUIStore((s) => s.addToast);

  // État partagé (store zustand) : AgentSelector, AssistantTopBar et la page
  // chat lisent/écrivent la MÊME instance — la sélection du sélecteur est
  // immédiatement reflétée dans le payload chat (`agent_id`).
  const selectedAgentId = useAgentStore((s) => s.selectedAgentId);
  const recentIds = useAgentStore((s) => s.recentAgentIds);
  const setSelection = useAgentStore((s) => s.setSelection);

  /**
   * Agent disparu (supprimé côté Core pendant que la préférence locale
   * pointait dessus) : repli explicite sur « Sans agent » + toast — jamais
   * un envoi vers un agent inexistant.
   */
  const validatedRef = useRef<string | null>(null);
  useEffect(() => {
    if (isLoading || agents.length === 0) return;
    if (!selectedAgentId || validatedRef.current === selectedAgentId) return;
    if (!agents.some((a) => a.id === selectedAgentId)) {
      validatedRef.current = null;
      setSelection(null, recentIds);
      addToast({
        type: "warning",
        message: "L'agent précédemment sélectionné n'est plus disponible.",
      });
    } else {
      validatedRef.current = selectedAgentId;
    }
  }, [agents, selectedAgentId, isLoading, addToast, setSelection, recentIds]);

  /** Sélection (id ou null = Sans agent), persistée via le store partagé. */
  const selectAgent = useCallback(
    (id: string | null) => {
      const nextRecent =
        id == null
          ? recentIds
          : [id, ...recentIds.filter((x) => x !== id)].slice(0, MAX_RECENT);
      setSelection(id, nextRecent);
    },
    [setSelection, recentIds],
  );

  const activeAgent: Agent | null =
    agents.find((a) => a.id === selectedAgentId) ?? null;

  return {
    /** Catalogue réel issu du Core. */
    agents,
    /** Agent actuellement actif, ou null (« Sans agent » / introuvable). */
    activeAgent,
    selectedAgentId,
    selectAgent,
    /** Ids des derniers agents utilisés (section Recent du sélecteur). */
    recentAgentIds: recentIds,
    agentsLoading: isLoading,
    agentsError: error,
  };
}
