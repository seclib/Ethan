import { create } from "zustand";
import type { Skill } from "@/types";

interface SkillsState {
  skills: Skill[];
  selectedSkill: Skill | null;
  isLoading: boolean;
  error: string | null;

  setSkills: (skills: Skill[]) => void;
  selectSkill: (id: string | null) => void;
  addSkill: (skill: Skill) => void;
  updateSkill: (id: string, updates: Partial<Skill>) => void;
  removeSkill: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useSkillsStore = create<SkillsState>((set, get) => ({
  skills: [],
  selectedSkill: null,
  isLoading: false,
  error: null,

  setSkills: (skills) => set({ skills }),

  selectSkill: (id) => {
    if (!id) {
      set({ selectedSkill: null });
      return;
    }
    const skill = get().skills.find((s) => s.id === id) || null;
    set({ selectedSkill: skill });
  },

  addSkill: (skill) =>
    set((state) => ({ skills: [...state.skills, skill] })),

  updateSkill: (id, updates) =>
    set((state) => ({
      skills: state.skills.map((s) => (s.id === id ? { ...s, ...updates } : s)),
      selectedSkill:
        state.selectedSkill?.id === id
          ? { ...state.selectedSkill, ...updates }
          : state.selectedSkill,
    })),

  removeSkill: (id) =>
    set((state) => ({
      skills: state.skills.filter((s) => s.id !== id),
      selectedSkill: state.selectedSkill?.id === id ? null : state.selectedSkill,
    })),

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));