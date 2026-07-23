"use client";

import { useState, useRef, useEffect } from "react";
import type { AssistantMessage, SessionMetrics } from "@/types/assistant";
import { AssistantMessageView } from "./assistant-message";
import { AssistantInput } from "./assistant-input";

interface AssistantChatProps {
  messages: AssistantMessage[];
  metrics: SessionMetrics;
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function AssistantChat({ messages, metrics, onSend, disabled }: AssistantChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 text-sm mt-20">
            <p className="text-lg mb-2">💬</p>
            <p>{`Commencez une conversation avec l'assistant`}</p>
          </div>
        )}
        {messages.map((msg) => (
          <AssistantMessageView key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <AssistantInput onSend={onSend} disabled={disabled} />
    </div>
  );
}