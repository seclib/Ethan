"use client";

import type { AssistantMessage } from "@/types/assistant";
import { ReasoningSection } from "./sections/reasoning-section";
import { ToolsSection } from "./sections/tools-section";
import { DocumentsSection } from "./sections/documents-section";
import { MemorySection } from "./sections/memory-section";
import { MessageFooter } from "./sections/message-footer";

interface AssistantMessageProps {
  message: AssistantMessage;
}

export function AssistantMessageView({ message }: AssistantMessageProps) {
  const isUser = message.role === "user";
  const time = new Date(message.timestamp).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] ${isUser ? "order-1" : "order-2"}`}>
        {/* Header */}
        <div className="flex items-center gap-2 mb-1 px-1">
          <span className={`text-xs font-medium ${isUser ? "text-accent" : "text-purple-400"}`}>
            {isUser ? "Vous" : "Assistant"}
          </span>
          <span className="text-xs text-muted-foreground">{time}</span>
        </div>

        {/* Bubble */}
        <div className={`
          rounded-lg px-4 py-3
          ${isUser
            ? "bg-accent-soft border border-accent-line"
            : "bg-background/40 border border-line-1/20"
          }
        `}>
          {/* Main content */}
          <p className="text-sm text-foreground whitespace-pre-wrap">{message.content}</p>

          {/* Assistant-only sections */}
          {!isUser && (
            <>
              <ReasoningSection steps={message.reasoning || []} />
              <DocumentsSection documents={message.documents || []} />
              <ToolsSection tools={message.tools || []} />
              <MemorySection entries={message.memoryEntries || []} />
              <MessageFooter
                durationMs={message.durationMs}
                cost={message.cost}
                tokensUsed={message.tokensUsed}
                tokensTotal={message.tokensTotal}
                model={message.model}
                provider={message.provider}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
