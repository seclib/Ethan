"use client";

import { useState, useCallback } from "react";
import type { AssistantMessage, SessionMetrics } from "@/types/assistant";
import { AssistantTopBar } from "@/components/assistant/assistant-top-bar";
import { AssistantSidePanel } from "@/components/assistant/assistant-side-panel";
import { AssistantChat } from "@/components/assistant/assistant-chat";

const INITIAL_METRICS: SessionMetrics = {
  agentName: "planner",
  agentStatus: "idle",
  model: "gemma3:4b",
  provider: "Ollama",
  cost: 0,
  duration: 0,
  tokensUsed: 0,
  tokensTotal: 8192,
};

export default function AssistantPage() {
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [metrics, setMetrics] = useState<SessionMetrics>(INITIAL_METRICS);
  const [disabled, setDisabled] = useState(false);

  const handleSend = useCallback(async (content: string) => {
    const userMessage: AssistantMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setDisabled(true);
    setMetrics((prev) => ({ ...prev, agentStatus: "run" }));

    try {
      // TODO: Replace with real API call
      // const response = await fetch("/api/chat", { ... });
      
      // Mock response for now
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      const assistantMessage: AssistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Réponse de l'assistant (à connecter au backend).",
        timestamp: Date.now(),
        reasoning: [
          "Analyser la requête utilisateur",
          "Consulter la mémoire contexte",
          "Appeler les outils nécessaires",
          "Générer la réponse",
        ],
        documents: [
          { name: "docker-compose.yml", type: "yaml", size: 2048 },
          { name: "README.md", type: "markdown", size: 4096 },
        ],
        tools: [
          { name: "memory.recall", durationMs: 120, status: "success" },
          { name: "web.search", durationMs: 850, status: "success" },
        ],
        memoryEntries: [
          { key: "memory:config:docker", relevance: 0.92, snippet: "Configuration Docker pour staging..." },
          { key: "memory:cred:aws", relevance: 0.78, snippet: "Credentials AWS région eu-west-1..." },
        ],
        durationMs: 1500,
        cost: 0.0023,
        tokensUsed: 847,
        tokensTotal: 8192,
        model: "gemma3:4b",
        provider: "Ollama",
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setMetrics((prev) => ({
        ...prev,
        agentStatus: "idle",
        duration: prev.duration + 1.5,
        cost: prev.cost + 0.0023,
        tokensUsed: prev.tokensUsed + 847,
      }));
    } catch (error) {
      console.error("Chat error:", error);
    } finally {
      setDisabled(false);
    }
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      <AssistantTopBar metrics={metrics} />
      <div className="flex-1 flex min-h-0">
        <AssistantChat messages={messages} metrics={metrics} onSend={handleSend} disabled={disabled} />
        <AssistantSidePanel
          documents={messages.flatMap((m) => m.documents || [])}
          memoryEntries={messages.flatMap((m) => m.memoryEntries || [])}
          tools={messages.flatMap((m) => m.tools || [])}
          mcpCalls={messages.flatMap((m) => m.mcpCalls || [])}
          actions={messages.flatMap((m) => m.actions || [])}
        />
      </div>
    </div>
  );
}