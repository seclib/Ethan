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
  onRenameChat: ((chatId: string, title: string) => void) | null;
  /** Conversation à ouvrir au prochain montage de la page chat
   *  (sélection déclenchée depuis la sidebar hors page chat). */
  pendingChatId: string | null;
  setPendingChat: (id: string | null) => void;
  /** Enregistrement par la page chat */
  setChatSidebar: (state: Partial<Omit<ChatSidebarState, "setChatSidebar" | "clearChatSidebar" | "pendingChatId" | "setPendingChat">>) => void;
  clearChatSidebar: () => void;
}

const emptyHandlers = {
  onNewChat: null,
  onSelectChat: null,
  onDeleteChat: null,
  onTogglePin: null,
  onRenameChat: null,
};

export const useChatSidebarStore = create<ChatSidebarState>((set) => ({
  chats: [],
  pinnedChats: [],
  regularChats: [],
  currentChatId: null,
  ...emptyHandlers,
  pendingChatId: null,
  setPendingChat: (id) => set({ pendingChatId: id }),
  setChatSidebar: (partial) => set(partial),
  clearChatSidebar: () =>
    set({
      // Sidebar conversation-centric (Open-WebUI) : les DONNÉES de
      // conversations restent visibles sur toutes les pages — seuls les
      // handlers branchés sur la page chat sont démontés.
      ...emptyHandlers,
    }),
}));
