import { create } from "zustand";
import { api, type SystemState, type Event, type Goal } from "./api";

export type AppPage =
  | "mission-control"
  | "goals"
  | "memory"
  | "skills"
  | "monitor"
  | "approvals"
  | "chat"
  | "config";

interface InspectorState {
  open: boolean;
  type: "goal" | "mission" | "skill" | "fact" | "event" | null;
  id: string | null;
  data: unknown | null;
}

interface AppState {
  state: SystemState | null;
  stateLoading: boolean;
  stateError: string | null;
  fetchState: () => Promise<void>;

  events: Event[];
  eventsLoading: boolean;
  fetchEvents: () => Promise<void>;

  goals: Goal[];
  goalsLoading: boolean;
  fetchGoals: () => Promise<void>;

  sidebarOpen: boolean;
  toggleSidebar: () => void;
  currentPage: AppPage;
  setPage: (page: AppPage) => void;
  theme: "dark" | "light";
  toggleTheme: () => void;

  inspector: InspectorState;
  openInspector: (type: InspectorState["type"], id: string, data?: unknown) => void;
  closeInspector: () => void;

  approvals: Approval[];
  addApproval: (a: Approval) => void;
  resolveApproval: (id: string, approved: boolean) => void;
}

export interface Approval {
  id: string;
  projectId: string;
  stepId: string;
  description: string;
  risk: "low" | "medium" | "high";
  budget: number;
  requestedBy: string;
  createdAt: string;
}

export const useStore = create<AppState>((set) => ({
  state: null,
  stateLoading: false,
  stateError: null,
  fetchState: async () => {
    set({ stateLoading: true, stateError: null });
    try {
      const state = await api.getState();
      set({ state, stateLoading: false });
    } catch (e) {
      set({ stateError: (e as Error).message, stateLoading: false });
    }
  },

  events: [],
  eventsLoading: false,
  fetchEvents: async () => {
    set({ eventsLoading: true });
    try {
      const { events } = await api.getEvents();
      set({ events, eventsLoading: false });
    } catch {
      set({ eventsLoading: false });
    }
  },

  goals: [],
  goalsLoading: false,
  fetchGoals: async () => {
    set({ goalsLoading: true });
    try {
      const { goals } = await api.getGoals();
      set({ goals, goalsLoading: false });
    } catch {
      set({ goalsLoading: false });
    }
  },

  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  currentPage: "mission-control",
  setPage: (page) => set({ currentPage: page }),
  theme: "dark",
  toggleTheme: () =>
    set((s) => {
      const next = s.theme === "dark" ? "light" : "dark";
      if (typeof document !== "undefined") {
        document.documentElement.classList.toggle("light", next === "light");
      }
      return { theme: next };
    }),

  inspector: { open: false, type: null, id: null, data: null },
  openInspector: (type, id, data) =>
    set({ inspector: { open: true, type, id, data: data ?? null } }),
  closeInspector: () =>
    set({ inspector: { open: false, type: null, id: null, data: null } }),

  approvals: [],
  addApproval: (a) => set((s) => ({ approvals: [...s.approvals, a] })),
  resolveApproval: (id, approved) =>
    set((s) => ({
      approvals: s.approvals.filter((a) => a.id !== id),
    })),
}));