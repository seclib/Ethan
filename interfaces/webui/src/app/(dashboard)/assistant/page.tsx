"use client";

import * as React from "react";
import { AssistantChat } from "@/features/assistant/components/assistant-chat";
import { AssistantTopBar } from "@/features/assistant/components/assistant-top-bar";
import { AssistantSidePanel } from "@/features/assistant/components/assistant-side-panel";
import { ChatSidebar } from "@/features/assistant/components/chat-sidebar";
import { useAgents } from "@/features/agents/hooks/use-agents";
import { useActiveModel } from "@/features/assistant/hooks/use-active-model";
import { useChats, type EthMessage } from "@/features/assistant/hooks/use-chats";
import type { AssistantMessage, SessionMetrics } from "@/types/assistant";
import { apiClient } from "@/core/api/api-client";

/** Convertir un message ETHAN (persistance Core) en message d'affichage. */
function toDisplayMessage(msg: EthMessage): AssistantMessage {
  const isUser = msg.role === "user";
  return {
    id: msg.id,
    role: isUser ? "user" : "assistant",
    content: msg.content,
    // `created_at` est une chaîne ISO — convertir en timestamp millisecondes
    timestamp: new Date(msg.created_at).getTime(),
  };
}

export default function AssistantPage() {
  const [isLoading, setIsLoading] = React.useState(false);
  const abortRef = React.useRef<AbortController | null>(null);
  const { agents } = useAgents();
  const { activeProvider, selectedProviderId, selectedModel, setModel } = useActiveModel();
  const { chats, messages, currentChatId, addMessage, createChat } = useChats();

  // Créer une conversation si aucune n'existe
  const hasCreatedRef = React.useRef(false);
  React.useEffect(() => {
    if (chats.length === 0 && !hasCreatedRef.current) {
      hasCreatedRef.current = true;
      createChat("Nouvelle conversation");
    }
  }, [chats.length, createChat]);

  // Conversion pour l'affichage
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

  const handleSend = async (content: string) => {
    if (!content.trim() || isLoading) return;

    const trimmed = content.trim();

    // Commande /model : affichage ou changement de modèle actif (local, non persisté)
    if (trimmed === "/model" || trimmed.startsWith("/model ")) {
      const parts = trimmed.split(/\s+/).slice(1);
      if (parts.length > 0) {
        setModel(parts[0]);
      }
      return;
    }

    // Persister le message utilisateur via le store ETHAN
    if (currentChatId) {
      addMessage(currentChatId, "user", trimmed);
    }
    setIsLoading(true);

    const abort = new AbortController();
    abortRef.current = abort;

    try {
      // Envoi du provider_id + modèle actifs au backend
      const res = await apiClient.request<{
        message: string;
        metadata?: { provider?: string; model?: string };
      }>("/api/v1/chat", {
        method: "POST",
        signal: abort.signal,
        body: JSON.stringify({
          message: trimmed,
          provider_id: selectedProviderId,
          model: selectedModel,
        }),
      });

      if (res.message && currentChatId) {
        // Persister la réponse assistant via le store ETHAN
        addMessage(currentChatId, "assistant", res.message);
      }
    } catch (error) {
      // Si annulé, afficher un message d'arrêt
      if (error instanceof DOMException && error.name === "AbortError") {
        if (currentChatId) {
          addMessage(currentChatId, "assistant", "⏹ Génération arrêtée.");
        }
        return;
      }
      if (currentChatId) {
        addMessage(currentChatId, "assistant", "Désolé, j'ai rencontré une erreur. Veuillez réessayer.");
      }
    } finally {
      abortRef.current = null;
      setIsLoading(false);
    }
  };

  const handleStop = () => {
    abortRef.current?.abort();
  };

  // Extract all data for side panel (à partir des messages persistés)
  const allDocuments = displayMessages.flatMap((m) => m.documents || []);
  const allMemory = displayMessages.flatMap((m) => m.memoryEntries || []);
  const allTools = displayMessages.flatMap((m) => m.tools || []);
  const allMcp = displayMessages.flatMap((m) => m.mcpCalls || []);
  const allActions = displayMessages.flatMap((m) => m.actions || []);

  return (
    <div className="flex h-full min-h-0 flex-col bg-background">
      <AssistantTopBar metrics={metrics} />

      <div className="flex flex-1 overflow-hidden">
        <ChatSidebar className="hidden md:flex" />

        <div className="flex-1 flex flex-col min-w-0">
          <AssistantChat
            messages={displayMessages}
            metrics={metrics}
            onSend={handleSend}
            onStop={handleStop}
            disabled={isLoading}
          />
        </div>

        <AssistantSidePanel
          documents={allDocuments}
          memoryEntries={allMemory}
          tools={allTools}
          mcpCalls={allMcp}
          actions={allActions}
        />
      </div>
    </div>
  );
}