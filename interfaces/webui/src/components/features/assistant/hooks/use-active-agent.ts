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

import { useCallback, useEffect, useRef, useState } from "react";
import { useAgents } from "@/components/features/agents/hooks/use-agents";
import { useUIStore } from "@/store/ui.store";
import type { Agent } from "@/types";

const STORAGE_AGENT = "ethan.active-agent";
const STORAGE_RECENT = "ethan.recent-agents";
const MAX_RECENT = 3;

/** Historique local des derniers agents utilisés (max 3 ids). */
function readRecentAgents(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_RECENT);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed)
      ? parsed.filter((id): id is string => typeof id === "string").slice(0, MAX_RECENT)
      : [];
  } catch {
    return [];
  }
}

export function useActiveAgent() {
  const { agents, isLoading, error } = useAgents();
  const addToast = useUIStore((s) => s.addToast);

  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(STORAGE_AGENT);
  });

  const [recentIds, setRecentIds] = useState<string[]>(readRecentAgents);

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
      setSelectedAgentId(null);
      window.localStorage.removeItem(STORAGE_AGENT);
      addToast({
        type: "warning",
        message: "L'agent précédemment sélectionné n'est plus disponible.",
      });
    } else {
      validatedRef.current = selectedAgentId;
    }
  }, [agents, selectedAgentId, isLoading, addToast]);

  const pushRecent = useCallback((id: string) => {
    setRecentIds((prev) => {
      const next = [id, ...prev.filter((x) => x !== id)].slice(0, MAX_RECENT);
      window.localStorage.setItem(STORAGE_RECENT, JSON.stringify(next));
      return next;
    });
  }, []);

  /** Sélection (id ou null = Sans agent), persistée localement. */
  const selectAgent = useCallback(
    (id: string | null) => {
      setSelectedAgentId(id);
      if (id == null) {
        window.localStorage.removeItem(STORAGE_AGENT);
      } else {
        window.localStorage.setItem(STORAGE_AGENT, id);
        pushRecent(id);
      }
    },
    [pushRecent],
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
