import { create } from "zustand";
import { agentsService } from "@/services/api-client";
import type { Agent } from "@/types";

interface AgentsState {
  agents: Agent[];
  selectedAgent: Agent | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchAgents: () => Promise<void>;
  selectAgent: (id: string) => void;
  createAgent: (data: { name: string; capabilities?: string[] }) => Promise<Agent>;
  updateAgent: (id: string, data: Partial<Agent>) => Promise<Agent>;
  deleteAgent: (id: string) => Promise<void>;
  clearError: () => void;
}

export const useAgentsStore = create<AgentsState>((set, get) => ({
  agents: [],
  selectedAgent: null,
  isLoading: false,
  error: null,

  fetchAgents: async () => {
    set({ isLoading: true, error: null });
    try {
      const agents = await agentsService.getAll();
      set({ agents, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch agents",
        isLoading: false,
      });
    }
  },

  selectAgent: (id) => {
    const agent = get().agents.find((a) => a.id === id) || null;
    set({ selectedAgent: agent });
  },

  createAgent: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const agent = await agentsService.create(data);
      set((state) => ({
        agents: [...state.agents, agent],
        isLoading: false,
      }));
      return agent;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to create agent";
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  updateAgent: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      const updated = await agentsService.update(id, data);
      set((state) => ({
        agents: state.agents.map((a) => (a.id === id ? updated : a)),
        selectedAgent: state.selectedAgent?.id === id ? updated : state.selectedAgent,
        isLoading: false,
      }));
      return updated;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to update agent";
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  deleteAgent: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await agentsService.delete(id);
      set((state) => ({
        agents: state.agents.filter((a) => a.id !== id),
        selectedAgent: state.selectedAgent?.id === id ? null : state.selectedAgent,
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to delete agent";
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));