import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * ETHAN Core — Modes conversationnels (source : core/chat/modes.py).
 * Le WebUI affiche et envoie — il ne résout jamais la logique de mode.
 * La priorité Core reste : request > session > mode profile > global.
 */
export type ChatModeValue = "plan" | "act" | "debug";

/**
 * Effort de raisonnement demandé (source : core/chat/modes.py ReasoningEffort).
 * ``none`` désactive explicitement ; le support réel est arbitré par Core selon
 * les capacités du modèle cible — le frontend n'envoie jamais de valeur fantôme.
 */
export type ReasoningEffortValue = "none" | "low" | "medium" | "high" | "xhigh";

export interface ChatModeMeta {
  /** Libellé affiché (FR). */
  label: string;
  /** Description pour la tooltip. */
  description: string;
  /** Icône lucide-react (nom). */
  icon: string;
  /** Couleur d'accent du badge. */
  color: string;
}

export const CHAT_MODES: Record<ChatModeValue, ChatModeMeta> = {
  plan: {
    label: "Plan",
    description: "Analyser, planifier, raisonner — lecture seule par défaut.",
    icon: "Calendar",
    color: "text-blue-400",
  },
  act: {
    label: "Act",
    description: "Exécuter, créer, modifier — selon les permissions Runtime.",
    icon: "Zap",
    color: "text-amber-400",
  },
  debug: {
    label: "Debug",
    description: "Diagnostiquer, investiguer — accès contrôlé aux diagnostics.",
    icon: "Bug",
    color: "text-purple-400",
  },
};

export const REASONING_EFFORTS: { value: ReasoningEffortValue; label: string }[] = [
  { value: "none", label: "None" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "xhigh", label: "Max" },
];

interface ChatModeState {
  /** Mode conversationnel actif (Act par défaut). */
  mode: ChatModeValue;
  /** Effort de raisonnement demandé au modèle. */
  reasoningEffort: ReasoningEffortValue;
  setMode: (mode: ChatModeValue) => void;
  setReasoningEffort: (effort: ReasoningEffortValue) => void;
}

/**
 * Source unique de vérité pour le mode de chat (front-only).
 * Partagé entre AssistantTopBar, ChatContextBar et la page chat.
 * La valeur est envoyée au backend via le payload chat (`mode` / `reasoning_effort`).
 */
export const useChatModeStore = create<ChatModeState>()(
  persist(
    (set) => ({
      mode: "act",
      reasoningEffort: "medium",
      setMode: (mode) => set({ mode }),
      setReasoningEffort: (reasoningEffort) => set({ reasoningEffort }),
    }),
    {
      name: "ethan.chat-mode",
      partialize: (s) => ({ mode: s.mode, reasoningEffort: s.reasoningEffort }),
    }
  )
);