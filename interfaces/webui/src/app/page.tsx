"use client";

import * as React from "react";
import { AssistantChat } from "@/components/features/assistant/components/assistant-chat";
import { AssistantTopBar } from "@/components/features/assistant/components/assistant-top-bar";
import { useChatSidebarStore } from "@/store/chat-sidebar.store";
import { useActiveModel } from "@/components/features/assistant/hooks/use-active-model";
import { useActiveAgent } from "@/components/features/assistant/hooks/use-active-agent";
import { useChats, type EthMessage } from "@/components/features/assistant/hooks/use-chats";
import { listCollections } from "@/lib/api/knowledge";
import { listSkills } from "@/lib/api/skills";
import { listTools } from "@/lib/api/tools";
import type { AssistantMessage, SessionMetrics } from "@/types/assistant";
import {
  ChatContextBar,
  type ChatContextItem,
} from "@/components/features/assistant/components/chat-context-bar";
import { useRouter } from "next/navigation";
import { useFacts } from "@/components/features/memory/hooks/use-memory";
import { useCreateGoal } from "@/components/features/goals/hooks/use-goals";

function toDisplayMessage(msg: EthMessage): AssistantMessage {
  const isUser = msg.role === "user";
  return {
    id: msg.id,
    role: isUser ? "user" : "assistant",
    content: msg.content,
    timestamp: new Date(msg.created_at).getTime(),
    status: msg.status,
    done: msg.done,
    // Appels d'outils (builtin/MCP) — source de vérité ETHAN Core.
    tools: msg.tools,
    mcpCalls: msg.metadata?.mcpCalls as AssistantMessage["mcpCalls"],
    model: msg.metadata?.model as string | undefined,
    provider: msg.metadata?.provider as string | undefined,
  };
}

export default function ChatHomePage() {
  // État agent UNIQUE (header [Agent ▼] ↔ composer ↔ payload) : le sélecteur
  // du header et les cases du composer partagent ce même état via props.
  const {
    agents,
    activeAgent,
    selectedAgentId,
    selectAgent,
    recentAgentIds,
    agentsLoading,
    agentsError,
  } = useActiveAgent();
  const { activeProvider, selectedProviderId, selectedModel, setModel } = useActiveModel();
  const {
    chats,
    pinnedChats,
    regularChats,
    messages,
    currentChatId,
    isLoading,
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

  // ── Catalogues (source : ETHAN Core via l'API) ─────────────────────────
  const [skills, setSkills] = React.useState<{ id: string; name: string }[]>([]);
  const [collections, setCollections] = React.useState<{ id: string; name: string }[]>([]);
  const [tools, setTools] = React.useState<{ id: string; name: string }[]>([]);

  // ── Sélections pour le chat (Open-WebUI style) ──────────────────────────
  const [selectedSkillIds, setSelectedSkillIds] = React.useState<string[]>([]);
  const [selectedCollectionIds, setSelectedCollectionIds] = React.useState<string[]>([]);
  const [selectedToolIds, setSelectedToolIds] = React.useState<string[]>([]);

  // ── Contexte actif (ChatContextBar rendue sous le header) ────────────────
  const [modelSelectorOpen, setModelSelectorOpen] = React.useState(false);
  /** Facts mémoire (hook dédié — cache partagé avec /workspace). */
  const { facts: memoryFacts } = useFacts();
  const router = useRouter();

  /**
   * Capacités RÉSOLUES pour l'affichage = UNION (agent ∪ sélection composer),
   * mêmes règles que core/chat/pipeline.py — recalculées ici UNIQUEMENT pour
   * rendre le contexte visible. Un id non résoluble dans un catalogue chargé
   * est exclu : la barre n'affiche jamais une capacité fantôme.
   */
  const resolveCapabilities = (
    manual: string[],
    fromAgent: unknown,
    catalog: { id: string; name: string; detail?: string }[],
  ): ChatContextItem[] => {
    const ids = Array.from(new Set([...manual, ...((fromAgent ?? []) as string[])]));
    return ids
      .map((id) => catalog.find((c) => c.id === id))
      .filter(
        (c): c is { id: string; name: string; detail?: string } => !!c,
      )
      .map(({ id, name, detail }) => (detail ? { id, name, detail } : { id, name }));
  };
  const activeTools = resolveCapabilities(
    selectedToolIds,
    activeAgent?.metadata?.tool_ids,
    tools.map((t) => ({ id: t.id, name: t.name, detail: (t as { badge?: string }).badge })),
  );
  const activeSkills = resolveCapabilities(
    selectedSkillIds,
    activeAgent?.skill_ids,
    skills,
  );
  const activeKnowledge = resolveCapabilities(
    selectedCollectionIds,
    activeAgent?.metadata?.knowledge_ids,
    collections,
  );

  // Charger les catalogues une seule fois au montage (source de vérité Core).
  React.useEffect(() => {
    let cancelled = false;
    Promise.allSettled([listSkills(), listCollections(), listTools()]).then(
      ([skillsRes, colsRes, toolsRes]) => {
        if (cancelled) return;
        if (skillsRes.status === "fulfilled") {
          setSkills(skillsRes.value.map((s) => ({ id: s.id, name: s.name })));
        }
        if (colsRes.status === "fulfilled") {
          setCollections(colsRes.value.map((c) => ({ id: c.id, name: c.name })));
        }
        if (toolsRes.status === "fulfilled") {
          setTools(toolsRes.value.map((t) => ({ id: t.id, name: t.name, badge: t.provider })));
        }
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  // Helpers de bascule de sélection (opérateur toggle sur les ensembles).
  const toggleSelection = (
    setter: React.Dispatch<React.SetStateAction<string[]>>,
    id: string,
  ) => {
    setter((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

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

  /**
   * Au chargement (refresh) : sélectionne automatiquement la conversation
   * la plus récente afin d'afficher l'historique existant — comportement
   * Open-WebUI. S'exécute aussi après la suppression de la conversation
   * courante (currentChatId repasse à null).
   */
  React.useEffect(() => {
    if (!currentChatId && chats.length > 0) {
      const latest = [...chats].sort((a, b) =>
        (b.updated_at || "").localeCompare(a.updated_at || ""),
      )[0];
      selectChat(latest.id);
    }
  }, [currentChatId, chats, selectChat]);

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

  const agentStatusMap: Record<string, "run" | "idle" | "error"> = {
    running: "run",
    idle: "idle",
    error: "error",
    paused: "idle",
    stopped: "idle",
  };
  
  const metrics: SessionMetrics = {
    // Vérité affichée = agent réellement actif (sélection header/composer),
    // plus le « premier agent de la liste ».
    agentName: activeAgent?.name || "ETHAN Core",
    agentStatus: agentStatusMap[activeAgent?.status || ""] || "idle",
    model: selectedModel || activeAgent?.model || "qwen2.5-coder",
    provider: activeProvider?.name || activeAgent?.provider || "ollama",
    cost: 0.0,
    duration: 0,
    tokensUsed: 0,
    tokensTotal: 0,
  };

  const currentChat = chats.find((c) => c.id === currentChatId);

  const handleNewChat = React.useCallback(async () => {
    await createChat("Nouvelle conversation");
  }, [createChat]);

    // Publie l'état des conversations vers l'AppSidebar du shell (la sidebar du
  // layout affiche les chats sur cette page).
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

  // Sélection déclenchée depuis la sidebar hors page chat (conversation-centric
  // Open-WebUI) : la navigation vers "/" est déjà faite, on ouvre la conversation.
  const pendingChatId = useChatSidebarStore((s) => s.pendingChatId);
  const setPendingChat = useChatSidebarStore((s) => s.setPendingChat);
  React.useEffect(() => {
    if (pendingChatId) {
      void selectChat(pendingChatId);
      setPendingChat(null);
    }
  }, [pendingChatId, selectChat, setPendingChat]);

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
      skill_ids: selectedSkillIds.length > 0 ? selectedSkillIds : undefined,
      tool_ids: selectedToolIds.length > 0 ? selectedToolIds : undefined,
      // Le backend (/v1/chat/completions/stream) lit knowledge_ids.
      knowledge_ids: selectedCollectionIds.length > 0 ? selectedCollectionIds : undefined,
      collection_ids: selectedCollectionIds.length > 0 ? selectedCollectionIds : undefined,
      // Routage Chat → Agent : résolu par le Core (provider/model/skills).
      agent_id: selectedAgentId ?? undefined,
      metadata: selectedAgentId ? { agent_id: selectedAgentId } : undefined,
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

  /** Mode Plan : soumet l'intention comme un goal réel (API /v1/goals).
   *  Les objectifs sont gérés par ETHAN Core — le bouton n'est pas un mock.
   */
  const createGoal = useCreateGoal();
  const handlePlan = (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return;
    createGoal.mutate({ title: trimmed.slice(0, 80), description: trimmed });
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
        <AssistantTopBar
          title={currentChat?.title || "Nouvelle conversation"}
          metrics={metrics}
          agents={agents}
          agentsLoading={agentsLoading}
          agentsError={agentsError}
          selectedAgentId={selectedAgentId}
          recentAgentIds={recentAgentIds}          onSelectAgent={selectAgent}
          modelSelectorOpen={modelSelectorOpen}
          onModelSelectorOpenChange={setModelSelectorOpen}
        />
        <ChatContextBar
          tools={activeTools}
          skills={activeSkills}
          knowledge={activeKnowledge}
          onCapabilityPageClick={(kind) =>
            router.push(
              kind === "tool" ? "/tools" : kind === "skill" ? "/skills" : "/knowledge",
            )
          }
          memoryFactCount={memoryFacts?.length ?? null}
          onMemoryClick={() => router.push("/workspace")}
        />
        <AssistantChat
          messages={displayMessages}
          metrics={metrics}
          chatId={currentChatId}
          isLoading={isLoading}
          onSend={handleSend}
          onStop={handleStop}
          disabled={isStreaming}
          onFileAttached={handleFileAttached}
          onPlan={handlePlan}
          error={error}
          onDismissError={clearError}
          onRegenerate={handleRegenerate}
          onEditMessage={handleEditMessage}
        />
      </div>
    </div>
  );
}