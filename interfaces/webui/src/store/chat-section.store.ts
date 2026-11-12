"use client";

/**
 * ETHAN WebUI — ChatSectionStore (front-only).
 *
 * Navigation par sections d'usage du Chat : Code / Apprendre / Créer / Écrire
 * / Vie quotidienne (parité avec les catégories de Claude Chat, à l'identité
 * ETHAN près). UI-only : aucune logique métier, aucun appel Core direct. Les
 * sections sont des catégories d'utilisation du Chat (filtres/contexte UX),
 * la conversation reste unique — aucune duplication de Chat.
 *
 * Extensible : de nouvelles sections peuvent être ajoutées sans refactor
 * (ajouter un id + libellé + icône dans CHAT_SECTIONS).
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ChatSectionId = "code" | "learn" | "create" | "write" | "daily";

export interface ChatSection {
  id: ChatSectionId;
  label: string;
  /** Icône lucide (nom) affichée dans la navigation. */
  icon: string;
  /** Invite affichée dans l'état vide du chat — PRESENTATION uniquement. */
  hint: string;
}

export const CHAT_SECTIONS: ChatSection[] = [
  {
    id: "code",
    label: "Code",
    icon: "Code",
    hint: "Écrivez, expliquez ou refactorisez du code — ETHAN peut aussi exécuter des outils.",
  },
  {
    id: "learn",
    label: "Apprendre",
    icon: "BookOpen",
    hint: "Explorez un sujet : ETHAN explique, structure et cite ses sources.",
  },
  {
    id: "create",
    label: "Créer",
    icon: "Palette",
    hint: "Rédigez, imaginez et itérez sur du contenu avec ETHAN.",
  },
  {
    id: "write",
    label: "Écrire",
    icon: "PenLine",
    hint: "Rédaction, reformulation, style : ETHAN écrit et corrige avec vous.",
  },
  {
    id: "daily",
    label: "Vie quotidienne",
    icon: "Coffee",
    hint: "Organisez vos tâches, notes et questions du quotidien.",
  },
];

/**
 * Métadonnées d'une section (libellé, icône, invite).
 * Lookup pur, sans état : utilisable au rendu sans abonnement au store.
 */
export function getChatSection(id: ChatSectionId): ChatSection {
  return CHAT_SECTIONS.find((s) => s.id === id) ?? CHAT_SECTIONS[0];
}

export interface ChatSectionState {
  activeSection: ChatSectionId;
  setSection: (id: ChatSectionId) => void;
}

export const useChatSectionStore = create<ChatSectionState>()(
  persist(
    (set) => ({
      activeSection: "code",
      setSection: (id) => set({ activeSection: id }),
    }),
    {
      name: "ethan-chat-section",
      partialize: (state) => ({ activeSection: state.activeSection }),
    }
  )
);