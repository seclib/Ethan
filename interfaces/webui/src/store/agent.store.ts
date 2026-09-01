import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AgentState {
  /** Agent actif (null = « Sans agent »). */
  selectedAgentId: string | null;
  /** Derniers agents utilisés (max 3, section Recent du sélecteur). */
  recentAgentIds: string[];
  setSelection: (agentId: string | null, recent: string[]) => void;
}

/**
 * Source unique de vérité pour la sélection d'agent. Partagée entre
 * AgentSelector, AssistantTopBar et la page chat (payload `agent_id`) —
 * une seule instance d'état pour toute l'application (zustand store),
 * symétrique de model.store.ts. Persistée pour la session suivante.
 */
export const useAgentStore = create<AgentState>()(
  persist(
    (set) => ({
      selectedAgentId: null,
      recentAgentIds: [],
      setSelection: (selectedAgentId, recentAgentIds) =>
        set({ selectedAgentId, recentAgentIds }),
    }),
    {
      name: "ethan.active-agent-store",
      partialize: (s) => ({
        selectedAgentId: s.selectedAgentId,
        recentAgentIds: s.recentAgentIds,
      }),
      // Migration : reprend les anciennes clés localStorage v1 du hook à
      // état local, puis les nettoie.
      onRehydrateStorage: () => (state) => {
        if (typeof window === "undefined" || !state) return;
        if (state.selectedAgentId == null) {
          const legacyAgent = window.localStorage.getItem("ethan.active-agent");
          let legacyRecent: string[] = [];
          try {
            const raw = window.localStorage.getItem("ethan.recent-agents");
            const parsed: unknown = raw ? JSON.parse(raw) : [];
            if (Array.isArray(parsed)) {
              legacyRecent = parsed
                .filter((id): id is string => typeof id === "string")
                .slice(0, 3);
            }
          } catch {
            /* préférence illisible : ignorée */
          }
          if (legacyAgent || legacyRecent.length > 0) {
            const recent = legacyAgent
              ? [legacyAgent, ...legacyRecent.filter((x) => x !== legacyAgent)].slice(0, 3)
              : legacyRecent;
            state.setSelection(legacyAgent, recent);
          }
        }
        window.localStorage.removeItem("ethan.active-agent");
        window.localStorage.removeItem("ethan.recent-agents");
      },
    }
  )
);
