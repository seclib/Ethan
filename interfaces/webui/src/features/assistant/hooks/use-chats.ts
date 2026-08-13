"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api/api-client";
import { useUIStore } from "@/core/store/ui.store";

export interface EthChat {
  id: string;
  title: string;
  user_id: string;
  folder_id: string | null;
  archived: boolean;
  pinned: boolean;
  share_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface EthMessage {
  id: string;
  chat_id: string;
  role: string;
  content: string;
  user_id: string;
  created_at: string;
}

const STORAGE_CURRENT_CHAT = "ethan.current-chat-id";

/**
 * Hook de persistance des conversations via core/state/chats.py.
 * ETHAN Core est la source de vérité — la WebUI ne fait qu'afficher/agir.
 */
export function useChats() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  // Liste des conversations
  const { data: chats = [], isLoading } = useQuery<EthChat[]>({
    queryKey: ["chats"],
    queryFn: () => apiClient.getChats(),
  });

  // Conversation active
  const { data: currentChatId } = useQuery<string>({
    queryKey: ["current-chat-id"],
    queryFn: () => {
      if (typeof window === "undefined") return "";
      return window.localStorage.getItem(STORAGE_CURRENT_CHAT) || "";
    },
    staleTime: Infinity,
  });

  // Messages de la conversation active
  const { data: messages = [] } = useQuery<EthMessage[]>({
    queryKey: ["chat-messages", currentChatId],
    queryFn: () => apiClient.getChatMessages(currentChatId as string),
    enabled: !!currentChatId,
  });

  const selectChat = (chatId: string) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_CURRENT_CHAT, chatId);
    }
    queryClient.invalidateQueries({ queryKey: ["current-chat-id"] });
  };

  const createChatMutation = useMutation({
    mutationFn: (title: string) =>
      apiClient.createChat({ title, user_id: "anonymous" }),
    onSuccess: (chat: EthChat) => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
      selectChat(chat.id);
      addToast({ type: "success", message: "Conversation créée" });
    },
    onError: () => {
      addToast({ type: "error", message: "Échec de création de la conversation" });
    },
  });

  const deleteChatMutation = useMutation({
    mutationFn: (chatId: string) => apiClient.deleteChat(chatId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
      queryClient.invalidateQueries({ queryKey: ["chat-messages"] });
      addToast({ type: "success", message: "Conversation supprimée" });
    },
    onError: () => {
      addToast({ type: "error", message: "Échec de suppression" });
    },
  });

  const addMessageMutation = useMutation({
    mutationFn: ({ chatId, role, content }: { chatId: string; role: string; content: string }) =>
      apiClient.addChatMessage(chatId, { role, content, user_id: "anonymous" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-messages", currentChatId] });
    },
    onError: () => {
      addToast({ type: "error", message: "Échec de l'envoi du message" });
    },
  });

  return {
    chats,
    messages,
    currentChatId,
    isLoading,
    selectChat,
    createChat: (title: string) => createChatMutation.mutate(title),
    deleteChat: (chatId: string) => deleteChatMutation.mutate(chatId),
    addMessage: (chatId: string, role: string, content: string) =>
      addMessageMutation.mutate({ chatId, role, content }),
  };
}