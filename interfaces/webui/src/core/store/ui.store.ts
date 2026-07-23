import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIState {
  // Sidebar
  sidebarExpanded: boolean;
  toggleSidebar: () => void;
  setSidebarExpanded: (expanded: boolean) => void;

  // Inspector
  inspectorOpen: boolean;
  inspector: { type: "agent" | "goal" | "mission" | null; id: string | null };
  toggleInspector: () => void;
  setInspectorOpen: (open: boolean) => void;
  openInspector: (type: "agent" | "goal" | "mission", id: string) => void;
  closeInspector: () => void;

  // Command Palette
  commandPaletteOpen: boolean;
  openCommandPalette: () => void;
  closeCommandPalette: () => void;

  // Mission Control
  missionControlOpen: boolean;
  setMissionControlOpen: (open: boolean) => void;
  toggleMissionControl: () => void;

  // Theme
  theme: "dark" | "light" | "system";
  setTheme: (theme: "dark" | "light" | "system") => void;

  // Loading states
  globalLoading: boolean;
  setGlobalLoading: (loading: boolean) => void;

  // Toasts
  toasts: Array<{
    id: string;
    type: "info" | "success" | "warning" | "error";
    message: string;
    duration?: number;
  }>;
  addToast: (toast: Omit<UIState["toasts"][0], "id">) => void;
  removeToast: (id: string) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Sidebar
      sidebarExpanded: false,
      toggleSidebar: () => set((state) => ({ sidebarExpanded: !state.sidebarExpanded })),
      setSidebarExpanded: (expanded) => set({ sidebarExpanded: expanded }),

      // Inspector
      inspectorOpen: false,
      inspector: { type: null, id: null },
      toggleInspector: () => set((state) => ({ inspectorOpen: !state.inspectorOpen })),
      setInspectorOpen: (open) => set({ inspectorOpen: open }),
      openInspector: (type, id) => set({ inspectorOpen: true, inspector: { type, id } }),
      closeInspector: () => set({ inspectorOpen: false, inspector: { type: null, id: null } }),

      // Command Palette
      commandPaletteOpen: false,
      openCommandPalette: () => set({ commandPaletteOpen: true }),
      closeCommandPalette: () => set({ commandPaletteOpen: false }),

      // Mission Control
      missionControlOpen: false,
      setMissionControlOpen: (open) => set({ missionControlOpen: open }),
      toggleMissionControl: () => set((state) => ({ missionControlOpen: !state.missionControlOpen })),

      // Theme
      theme: "dark",
      setTheme: (theme) => set({ theme }),

      // Loading states
      globalLoading: false,
      setGlobalLoading: (loading) => set({ globalLoading: loading }),

      // Toasts
      toasts: [],
      addToast: (toast) => {
        const id = Math.random().toString(36).substring(7);
        set((state) => ({
          toasts: [...state.toasts, { ...toast, id }],
        }));

        // Auto-remove toast after duration
        if (toast.duration !== 0) {
          setTimeout(() => {
            set((state) => ({
              toasts: state.toasts.filter((t) => t.id !== id),
            }));
          }, toast.duration || 5000);
        }
      },
      removeToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),
    }),
    {
      name: "ethan-ui-storage",
      partialize: (state) => ({
        sidebarExpanded: state.sidebarExpanded,
        theme: state.theme,
      }),
    }
  )
);