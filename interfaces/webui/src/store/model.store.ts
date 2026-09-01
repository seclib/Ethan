import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ModelState {
  /** Provider actif ("" = non résolu → fallback sur le provider par défaut Core). */
  selectedProviderId: string;
  /** Modèle actif (identifiant renvoyé par /providers/{id}/models). */
  selectedModel: string;
  setSelection: (providerId: string, model: string) => void;
  setModel: (model: string) => void;
}

/**
 * Source unique de vérité pour la sélection moteur IA (provider + modèle).
 * Partagée entre ModelSelector, ProviderSelector, AssistantTopBar et la page
 * chat — une seule instance d'état pour toute l'application (zustand store).
 * Persistée pour retrouver la préférence à la session suivante.
 */
export const useModelStore = create<ModelState>()(
  persist(
    (set) => ({
      selectedProviderId: "",
      selectedModel: "",
      setSelection: (selectedProviderId, selectedModel) =>
        set({ selectedProviderId, selectedModel }),
      setModel: (selectedModel) => set({ selectedModel }),
    }),
    {
      name: "ethan.active-engine",
      partialize: (s) => ({
        selectedProviderId: s.selectedProviderId,
        selectedModel: s.selectedModel,
      }),
      // Migration : reprend l'ancienne préférence (clés localStorage v1) si
      // le nouveau store est vide, puis nettoie les anciennes clés.
      onRehydrateStorage: () => (state) => {
        if (typeof window === "undefined" || !state) return;
        if (!state.selectedProviderId) {
          const legacyProvider = window.localStorage.getItem("ethan.active-provider");
          const legacyModel = window.localStorage.getItem("ethan.active-model");
          if (legacyProvider || legacyModel) {
            state.setSelection(legacyProvider || "", legacyModel || "");
          }
        }
        window.localStorage.removeItem("ethan.active-provider");
        window.localStorage.removeItem("ethan.active-model");
      },
    }
  )
);
