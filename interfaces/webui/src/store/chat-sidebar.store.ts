"use client";

import { create } from "zustand";
import type { EthChat } from "@/components/features/assistant/hooks/use-chats";

/**
 * Pont entre la page chat (/) et l'AppSidebar du shell.
 * Odysseus n'a qu'UNE sidebar : sur la page chat elle affiche les
 * conversations, sinon la navigation. Ce store permet au shell de
 * rendre la vue Chats sans dupliquer l'état de useChats().
 */

export interface ChatSidebarState {
  /** Données des conversations */
  chats: EthChat[];
  pinnedChats: EthChat[];
  regularChats: EthChat[];
  currentChatId: string | null;
  /** Handlers fournis par la page chat (null = vue chat inactive) */
  onNewChat: (() => void) | null;
  onSelectChat: ((chatId: string) => void) | null;
  onDeleteChat: ((chatId: string) => void) | null;
  onTogglePin: ((chatId: string, currentPinned: boolean) => void) | null;
  /** Enregistrement par la page chat */
  setChatSidebar: (state: Partial<Omit<ChatSidebarState, "setChatSidebar" | "clearChatSidebar">>) => void;
  clearChatSidebar: () => void;
}

const emptyHandlers = {
  onNewChat: null,
  onSelectChat: null,
  onDeleteChat: null,
  onTogglePin: null,
};

export const useChatSidebarStore = create<ChatSidebarState>((set) => ({
  chats: [],
  pinnedChats: [],
  regularChats: [],
  currentChatId: null,
  ...emptyHandlers,
  setChatSidebar: (partial) => set(partial),
  clearChatSidebar: () =>
    set({
      chats: [],
      pinnedChats: [],
      regularChats: [],
      currentChatId: null,
      ...emptyHandlers,
    }),
}));
