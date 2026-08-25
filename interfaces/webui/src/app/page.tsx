"use client";

import * as React from "react";
import { AssistantChat } from "@/components/features/assistant/components/assistant-chat";
import { AssistantTopBar } from "@/components/features/assistant/components/assistant-top-bar";
import { useChatSidebarStore } from "@/store/chat-sidebar.store";
import { useAgents } from "@/components/features/agents/hooks/use-agents";
import { useActiveModel } from "@/components/features/assistant/hooks/use-active-model";
import { useChats, type EthMessage } from "@/components/features/assistant/hooks/use-chats";
import { listCollections } from "@/lib/api/knowledge";
import type { AssistantMessage, SessionMetrics } from "@/types/assistant";

function toDisplayMessage(msg: EthMessage): AssistantMessage {
  const isUser = msg.role === "user";
  return {
    id: msg.id,
    role: isUser ? "user" : "assistant",
    content: msg.content,
    timestamp: new Date(msg.created_at).getTime(),
    status: msg.status,
    done: msg.done,
  };
}

export default function ChatHomePage() {
  const { agents } = useAgents();
  const { activeProvider, selectedProviderId, selectedModel, setModel } = useActiveModel();
  const {
    chats,
    pinnedChats,
    regularChats,
    messages,
    currentChatId,
    createChat,
    loadChats,
    loadChat,
    selectChat,
    deleteChat,
    renameChat,
    togglePin,
    sendMessageStream,
    stopGeneration,
    isStreaming,
    error,
    clearError,
  } = useChats();
  const [attachedFileIds, setAttachedFileIds] = React.useState<string[]>([]);
  const [attachedFileNames, setAttachedFileNames] = React.useState<string[]>([]);
  const [toolsEnabled, setToolsEnabled] = React.useState(false);
  const [agentEnabled, setAgentEnabled] = React.useState(false);
  const [knowledgeEnabled, setKnowledgeEnabled] = React.useState(false);
  const [selectedAgentId, setSelectedAgentId] = React.useState<string | null>(null);
  const [selectedCollectionIds, setSelectedCollectionIds] = React.useState<string[]>([]);
  const [selectedToolIds, setSelectedToolIds] = React.useState<string[]>([]);

  // Collections knowledge chargées à l'activation du toggle (source : Core).
  React.useEffect(() => {
    if (!knowledgeEnabled || selectedCollectionIds.length > 0) return;
    let cancelled = false;
    listCollections()
      .then((collections) => {
        if (!cancelled) setSelectedCollectionIds(collections.map((c) => c.id));
      })
      .catch(() => {
        // Pas de collections disponibles : le toggle restera sans effet RAG.
      });
    return () => {
      cancelled = true;
    };
  }, [knowledgeEnabled, selectedCollectionIds.length]);

  // Load chats on mount
  React.useEffect(() => {
    loadChats();
  }, [loadChats]);

  const hasCreatedRef = React.useRef(false);
  React.useEffect(() => {
    if (chats.length === 0 && !hasCreatedRef.current) {
      hasCreatedRef.current = true;
      createChat("Nouvelle conversation");
    }
  }, [chats.length, createChat]);

  // Load messages when a chat is selected
  React.useEffect(() => {
    if (currentChatId) {
      loadChat(currentChatId);
    }
  }, [currentChatId, loadChat]);

  const displayMessages: AssistantMessage[] = React.useMemo(
    () => messages.map(toDisplayMessage),
    [messages]
  );

  const primaryAgent = agents?.[0];
  const agentStatusMap: Record<string, "run" | "idle" | "error"> = {
    running: "run",
    idle: "idle",
    error: "error",
    paused: "idle",
    stopped: "idle",
  };
  
  const metrics: SessionMetrics = {
    agentName: primaryAgent?.name || "ETHAN Core",
    agentStatus: agentStatusMap[primaryAgent?.status || ""] || "idle",
    model: selectedModel || primaryAgent?.model || "qwen2.5-coder",
    provider: activeProvider?.name || primaryAgent?.provider || "ollama",
    cost: 0.0,
    duration: 0,
    tokensUsed: 0,
    tokensTotal: 0,
  };

  const currentChat = chats.find((c) => c.id === currentChatId);

  const handleNewChat = async () => {
    await createChat("Nouvelle conversation");
  };

  // Publie l'état des conversations vers l'AppSidebar du shell (modèle Odysseus :
  // la sidebar du layout affiche les chats sur cette page).
  const setChatSidebar = useChatSidebarStore((s) => s.setChatSidebar);
  const clearChatSidebar = useChatSidebarStore((s) => s.clearChatSidebar);
  React.useEffect(() => {
    setChatSidebar({
      chats,
      pinnedChats,
      regularChats,
      currentChatId,
      onNewChat: handleNewChat,
      onSelectChat: selectChat,
      onDeleteChat: deleteChat,
      onTogglePin: togglePin,
      onRenameChat: renameChat,
    });
    return () => clearChatSidebar();
  }, [chats, pinnedChats, regularChats, currentChatId, handleNewChat, selectChat, deleteChat, togglePin, renameChat, setChatSidebar, clearChatSidebar]);

  /**
   * Flux d'envoi partagé : message simple, régénération (renvoi du dernier
   * message utilisateur) et édition (renvoi du contenu modifié) passent
   * tous par ici — un seul point de vérité pour le streaming.
   */
  const runStream = async (content: string) => {
    if (!content.trim() || isStreaming) return;
    const trimmed = content.trim();

    const generator = sendMessageStream({
      message: trimmed,
      chat_id: currentChatId ?? undefined,
      provider_id: selectedProviderId ?? undefined,
      model: selectedModel ?? undefined,
      file_ids: attachedFileIds.length > 0 ? attachedFileIds : undefined,
      tool_ids: toolsEnabled && selectedToolIds.length > 0 ? selectedToolIds : undefined,
      // Le backend (/v1/chat/completions/stream) lit knowledge_ids.
      knowledge_ids: knowledgeEnabled && selectedCollectionIds.length > 0 ? selectedCollectionIds : undefined,
      collection_ids: knowledgeEnabled && selectedCollectionIds.length > 0 ? selectedCollectionIds : undefined,
      metadata: agentEnabled && selectedAgentId ? { agent_id: selectedAgentId } : undefined,
    });

    setAttachedFileIds([]);
    setAttachedFileNames([]);

    try {
      for await (const event of generator) {
        // Le backend titre la conversation d'après le 1er message :
        // on rafraîchit l'historique à la fin de chaque génération.
        if ((event as Record<string, unknown>).type === "done") {
          loadChats();
        }
      }
    } catch (error) {
      // Les erreurs de flux sont déjà capturées dans use-chats (état error).
      console.error("Chat streaming failed:", error);
    }
  };

  const handleSend = (content: string) => {
    const trimmed = content.trim();
    if (trimmed === "/model" || trimmed.startsWith("/model ")) {
      const parts = trimmed.split(/\s+/).slice(1);
      if (parts.length > 0) {
        setModel(parts[0]);
      }
      return;
    }
    runStream(trimmed);
  };

  /** Arrêt réel : avorte le flux SSE, conserve le contenu partiel reçu. */
  const handleStop = () => {
    stopGeneration();
  };

  /**
   * Régénération : renvoie le contenu du dernier message utilisateur
   * précédant la réponse visée. Le backend crée une nouvelle branche
   * (arbre de messages ChatStore) — l'ancienne réponse est conservée.
   */
  const handleRegenerate = (assistantMessageId: string) => {
    if (isStreaming) return;
    const index = messages.findIndex((m) => m.id === assistantMessageId);
    if (index === -1) return;
    for (let i = index - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        runStream(messages[i].content);
        return;
      }
    }
  };

  /** Édition d'un message utilisateur : renvoi du contenu modifié (nouvelle branche). */
  const handleEditMessage = (messageId: string, newContent: string) => {
    if (isStreaming) return;
    const target = messages.find((m) => m.id === messageId);
    if (!target || target.role !== "user") return;
    runStream(newContent);
  };

  const handleFileAttached = (fileId: string, filename: string) => {
    setAttachedFileIds((prev) => [...prev, fileId]);
    setAttachedFileNames((prev) => [...prev, filename]);
  };

  return (
    <div className="flex h-full min-h-0 w-full">
      <div className="flex h-full min-h-0 flex-1 flex-col">
        <AssistantTopBar title={currentChat?.title || "Nouvelle conversation"} metrics={metrics} />
        <AssistantChat
          messages={displayMessages}
          metrics={metrics}
          onSend={handleSend}
          onStop={handleStop}
          disabled={isStreaming}
          onFileAttached={handleFileAttached}
          toolsEnabled={toolsEnabled}
          agentEnabled={agentEnabled}
          knowledgeEnabled={knowledgeEnabled}
          onToggleTools={() => setToolsEnabled((v) => !v)}
          onToggleAgent={() => setAgentEnabled((v) => !v)}
          onToggleKnowledge={() => setKnowledgeEnabled((v) => !v)}
          error={error}
          onDismissError={clearError}
          onRegenerate={handleRegenerate}
          onEditMessage={handleEditMessage}
        />
      </div>
    </div>
  );
}