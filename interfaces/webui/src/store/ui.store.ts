import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIState {
  // Sidebar
  /** État runtime (ce qui est rendu). Toujours `true` au boot. */
  sidebarExpanded: boolean;
  /**
   * Préférence explicite de l'utilisateur (persistée). `null` = aucune
   * préférence → la sidebar est DÉPLOYÉE par défaut à chaque session.
   * Le collapse automatique mobile n'écrit JAMAIS cette préférence.
   */
  sidebarPreference: boolean | null;
  toggleSidebar: () => void;
  setSidebarExpanded: (expanded: boolean, persistPreference?: boolean) => void;

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

  // Mail floating window (fenêtre superposée)
  mailPanelOpen: boolean;
  setMailPanelOpen: (open: boolean) => void;
  toggleMailPanel: () => void;

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
      sidebarExpanded: true,
      sidebarPreference: null,
      // Action utilisateur (bouton collapse/expand) → mémorise la préférence.
      toggleSidebar: () =>
        set((state) => ({
          sidebarExpanded: !state.sidebarExpanded,
          sidebarPreference: !state.sidebarExpanded,
        })),
      // Changement programmatique (responsive, overlay…) : ne persiste que si demandé.
      setSidebarExpanded: (expanded, persistPreference = false) =>
        set((state) => ({
          sidebarExpanded: expanded,
          ...(persistPreference ? { sidebarPreference: expanded } : {}),
        })),

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

      // Mail floating window
      mailPanelOpen: false,
      setMailPanelOpen: (open: boolean) => set({ mailPanelOpen: open }),
      toggleMailPanel: () => set((state) => ({ mailPanelOpen: !state.mailPanelOpen })),

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
        // Seule la préférence EXPLICITE est persistée — jamais l'état runtime,
        // afin qu'une session neuve démarre toujours avec la sidebar déployée
        // sauf choix explicite de l'utilisateur.
        sidebarPreference: state.sidebarPreference,
      }),
      // À l'hydratation : applique la préférence explicite s'il y en a une.
      onRehydrateStorage: () => (state) => {
        if (state && state.sidebarPreference !== null) {
          state.sidebarExpanded = state.sidebarPreference;
        }
      },
    }
  )
);