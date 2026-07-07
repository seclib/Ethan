import { create } from "zustand";
import type { Fact, MemoryEvent } from "@/types";

interface MemoryState {
  facts: Fact[];
  events: MemoryEvent[];
  selectedFact: Fact | null;
  isLoading: boolean;
  error: string | null;

  setFacts: (facts: Fact[]) => void;
  setEvents: (events: MemoryEvent[]) => void;
  selectFact: (id: string | null) => void;
  addFact: (fact: Fact) => void;
  updateFact: (id: string, updates: Partial<Fact>) => void;
  addEvent: (event: MemoryEvent) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useMemoryStore = create<MemoryState>((set, get) => ({
  facts: [],
  events: [],
  selectedFact: null,
  isLoading: false,
  error: null,

  setFacts: (facts) => set({ facts }),

  setEvents: (events) => set({ events }),

  selectFact: (id) => {
    if (!id) {
      set({ selectedFact: null });
      return;
    }
    const fact = get().facts.find((f) => f.id === id) || null;
    set({ selectedFact: fact });
  },

  addFact: (fact) =>
    set((state) => ({ facts: [...state.facts, fact] })),

  updateFact: (id, updates) =>
    set((state) => ({
      facts: state.facts.map((f) => (f.id === id ? { ...f, ...updates } : f)),
      selectedFact:
        state.selectedFact?.id === id
          ? { ...state.selectedFact, ...updates }
          : state.selectedFact,
    })),

  addEvent: (event) =>
    set((state) => ({ events: [...state.events, event] })),

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));