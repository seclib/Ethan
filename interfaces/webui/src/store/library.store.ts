import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * ETHAN WebUI — Préférences d'interface de la Library.
 *
 * Préférence PUREMENT interface (navigation/affichage) : le mode d'affichage
 * par défaut de la bibliothèque. Elle est consommée par `LibraryWorkspace`
 * (onglet « Library » de /knowledge) ET par la section Settings → Library —
 * une seule source de vérité, aucune logique métier (les données restent
 * servies par le Core).
 */
export type LibraryViewMode = "grid" | "list";

interface LibraryPrefsState {
  /** Mode d'affichage par défaut de la Library. */
  viewMode: LibraryViewMode;
  setViewMode: (viewMode: LibraryViewMode) => void;
}

export const useLibraryStore = create<LibraryPrefsState>()(
  persist(
    (set) => ({
      viewMode: "grid",
      setViewMode: (viewMode) => set({ viewMode }),
    }),
    {
      name: "ethan.library-prefs",
      partialize: (s) => ({ viewMode: s.viewMode }),
    }
  )
);
