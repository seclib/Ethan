"use client";

import * as React from "react";
import { AssistantChat } from "@/features/assistant/components/assistant-chat";
import { AssistantTopBar } from "@/features/assistant/components/assistant-top-bar";
import { AssistantSidePanel } from "@/features/assistant/components/assistant-side-panel";
import { useAgents } from "@/features/agents/hooks/use-agents";
import type { AssistantMessage, SessionMetrics } from "@/types/assistant";
import { apiClient } from "@/core/api/api-client";

export default function AssistantPage() {
  const [messages, setMessages] = React.useState<AssistantMessage[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const { agents } = useAgents();

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
    model: primaryAgent?.model || "claude-3-opus",
    provider: primaryAgent?.provider || "anthropic",
    cost: 0.0,
    duration: 0,
    tokensUsed: 0,
    tokensTotal: 0,
  };

  const handleSend = async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: AssistantMessage = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Temporary fallback call until real backend is mapped
      const res = await apiClient.request<{ reply: string }>("/api/v1/chat", {
        method: "POST",
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (res.reply) {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: res.reply,
            timestamp: Date.now(),
          },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Désolé, j'ai rencontré une erreur. Veuillez réessayer.",
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Extract all data for side panel
  const allDocuments = messages.flatMap(m => m.documents || []);
  const allMemory = messages.flatMap(m => m.memoryEntries || []);
  const allTools = messages.flatMap(m => m.tools || []);
  const allMcp = messages.flatMap(m => m.mcpCalls || []);
  const allActions = messages.flatMap(m => m.actions || []);

  return (
    <div className="flex h-full min-h-0 flex-col bg-background">
      <AssistantTopBar metrics={metrics} />
      
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 flex flex-col min-w-0">
          <AssistantChat 
            messages={messages} 
            metrics={metrics}
            onSend={handleSend} 
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
