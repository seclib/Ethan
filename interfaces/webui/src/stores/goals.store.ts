import { create } from "zustand";
import { goalsService } from "@/services/api-client";
import type { Goal, Task } from "@/types";

interface GoalsState {
  goals: Goal[];
  selectedGoal: Goal | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchGoals: () => Promise<void>;
  selectGoal: (id: string) => void;
  createGoal: (data: { title: string; description?: string; priority?: string }) => Promise<Goal>;
  updateGoal: (id: string, data: Partial<Goal>) => Promise<Goal>;
  deleteGoal: (id: string) => Promise<void>;
  clearError: () => void;
}

export const useGoalsStore = create<GoalsState>((set, get) => ({
  goals: [],
  selectedGoal: null,
  isLoading: false,
  error: null,

  fetchGoals: async () => {
    set({ isLoading: true, error: null });
    try {
      const goals = await goalsService.getAll();
      set({ goals, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch goals",
        isLoading: false,
      });
    }
  },

  selectGoal: (id) => {
    const goal = get().goals.find((g) => g.id === id) || null;
    set({ selectedGoal: goal });
  },

  createGoal: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const goal = await goalsService.create(data);
      set((state) => ({
        goals: [...state.goals, goal],
        isLoading: false,
      }));
      return goal;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to create goal";
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  updateGoal: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      const updated = await goalsService.update(id, data);
      set((state) => ({
        goals: state.goals.map((g) => (g.id === id ? updated : g)),
        selectedGoal: state.selectedGoal?.id === id ? updated : state.selectedGoal,
        isLoading: false,
      }));
      return updated;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to update goal";
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  deleteGoal: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await goalsService.delete(id);
      set((state) => ({
        goals: state.goals.filter((g) => g.id !== id),
        selectedGoal: state.selectedGoal?.id === id ? null : state.selectedGoal,
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to delete goal";
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },


  clearError: () => set({ error: null }),
}));