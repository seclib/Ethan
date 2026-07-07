import { create } from "zustand";
import type { Mission, Step } from "@/types";

interface MissionsState {
  missions: Mission[];
  selectedMission: Mission | null;
  isLoading: boolean;
  error: string | null;

  setMissions: (missions: Mission[]) => void;
  selectMission: (id: string | null) => void;
  updateMission: (id: string, updates: Partial<Mission>) => void;
  updateStep: (missionId: string, stepId: string, updates: Partial<Step>) => void;
  addMission: (mission: Mission) => void;
  removeMission: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useMissionsStore = create<MissionsState>((set, get) => ({
  missions: [],
  selectedMission: null,
  isLoading: false,
  error: null,

  setMissions: (missions) => set({ missions }),

  selectMission: (id) => {
    if (!id) {
      set({ selectedMission: null });
      return;
    }
    const mission = get().missions.find((m) => m.id === id) || null;
    set({ selectedMission: mission });
  },

  updateMission: (id, updates) => {
    set((state) => ({
      missions: state.missions.map((m) =>
        m.id === id ? { ...m, ...updates } : m
      ),
      selectedMission:
        state.selectedMission?.id === id
          ? { ...state.selectedMission, ...updates }
          : state.selectedMission,
    }));
  },

  updateStep: (missionId, stepId, updates) => {
    set((state) => {
      const updateSteps = (steps: Step[]) =>
        steps.map((s) => (s.id === stepId ? { ...s, ...updates } : s));

      return {
        missions: state.missions.map((m) =>
          m.id === missionId ? { ...m, steps: updateSteps(m.steps) } : m
        ),
        selectedMission:
          state.selectedMission?.id === missionId
            ? {
                ...state.selectedMission,
                steps: updateSteps(state.selectedMission.steps),
              }
            : state.selectedMission,
      };
    });
  },

  addMission: (mission) =>
    set((state) => ({ missions: [...state.missions, mission] })),

  removeMission: (id) =>
    set((state) => ({
      missions: state.missions.filter((m) => m.id !== id),
      selectedMission:
        state.selectedMission?.id === id ? null : state.selectedMission,
    })),

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));