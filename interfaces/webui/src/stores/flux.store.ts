import { create } from "zustand";
import type { FluxEvent } from "@/types";

interface FluxState {
  events: FluxEvent[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;

  setEvents: (events: FluxEvent[]) => void;
  addEvent: (event: FluxEvent) => void;
  clearEvents: () => void;
  setConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useFluxStore = create<FluxState>((set) => ({
  events: [],
  isConnected: false,
  isLoading: false,
  error: null,

  setEvents: (events) => set({ events }),

  addEvent: (event) =>
    set((state) => ({
      events: [event, ...state.events].slice(0, 500), // Keep max 500 events
    })),

  clearEvents: () => set({ events: [] }),

  setConnected: (connected) => set({ isConnected: connected }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),
}));