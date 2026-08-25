"use client";

import { useState, useRef, useEffect } from "react";
import type { AssistantMessage, SessionMetrics } from "@/types/assistant";
import { AssistantMessageView } from "./assistant-message";
import { AssistantInput } from "./assistant-input";
import { TypingIndicator } from "./typing-indicator";

interface AssistantChatProps {
  messages: AssistantMessage[];
  metrics: SessionMetrics;
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  onFileAttached?: (fileId: string, filename: string) => void;
  onToggleTools?: () => void;
  onToggleAgent?: () => void;
  onToggleKnowledge?: () => void;
  toolsEnabled?: boolean;
  agentEnabled?: boolean;
  knowledgeEnabled?: boolean;
}

export function AssistantChat({
  messages,
  metrics,
  onSend,
  onStop,
  disabled,
  onFileAttached,
  onToggleTools,
  onToggleAgent,
  onToggleKnowledge,
  toolsEnabled,
  agentEnabled,
  knowledgeEnabled,
}: AssistantChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center text-center mt-24 px-4">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10">
                <span className="text-2xl font-bold text-accent">O</span>
              </div>
              <h2 className="text-xl font-semibold text-foreground">ETHAN</h2>
              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                Posez une question, demandez une analyse, ou lancez une tâche.
              </p>
            </div>
          )}
          {messages.map((msg) => (
            <AssistantMessageView key={msg.id} message={msg} />
          ))}
          {disabled && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <AssistantInput
        onSend={onSend}
        onStop={onStop}
        disabled={disabled}
        onFileAttached={onFileAttached}
        onToggleTools={onToggleTools}
        onToggleAgent={onToggleAgent}
        onToggleKnowledge={onToggleKnowledge}
        toolsEnabled={toolsEnabled}
        agentEnabled={agentEnabled}
        knowledgeEnabled={knowledgeEnabled}
      />
    </div>
  );
}
