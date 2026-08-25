"use client";

import * as React from "react";
import type { AssistantMessage } from "@/types/assistant";
import { ReasoningSection } from "./sections/reasoning-section";
import { ToolsSection } from "./sections/tools-section";
import { DocumentsSection } from "./sections/documents-section";
import { MemorySection } from "./sections/memory-section";
import { MessageFooter } from "./sections/message-footer";
import { MessageActions } from "./message-actions";
import { MarkdownContent } from "./markdown-content";
import { speakText } from "@/lib/api/audio";
import { Volume2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface AssistantMessageProps {
  message: AssistantMessage;
}

/** Bouton lecture vocale — synthèse déléguée à ETHAN Core (/v1/audio/synthesize). */
function SpeakButton({ text }: { text: string }) {
  const [speaking, setSpeaking] = React.useState(false);
  return (
    <button
      onClick={async () => {
        if (speaking) return;
        setSpeaking(true);
        try {
          await speakText(text);
        } catch {
          // erreur silencieuse : le pipeline TTS n'est peut-être pas configuré
        } finally {
          setSpeaking(false);
        }
      }}
      className="p-1 rounded hover:bg-bg-1 text-foreground-tertiary opacity-0 group-hover:opacity-100 transition-opacity"
      title="Lire à voix haute"
      aria-label="Lire à voix haute"
    >
      {speaking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Volume2 className="h-4 w-4" />}
    </button>
  );
}

/**
 * Message renderé selon le visual language Open-WebUI :
 * - Assistant : contenu en ligne (pas de bulle colorée), avatar rond au-dessus
 * - User      : bulle discrète alignée à droite (fond neutre, non accent)
 */
export function AssistantMessageView({ message }: AssistantMessageProps) {
  const isUser = message.role === "user";
  const time = new Date(message.timestamp).toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "group relative flex w-full gap-3",
          isUser ? "flex-row-reverse" : "flex-row"
        )}
      >
        {/* Avatar (Claude/ChatGPT style) */}
        {!isUser && (
          <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/10 text-[10px] font-bold text-accent">
            O
          </div>
        )}

        <div
          className={cn(
            "min-w-0 flex-1",
            isUser ? "max-w-[80%]" : "max-w-full"
          )}
        >
          {/* Header */}
          <div className="mb-1 flex items-center gap-2 px-1">
            <span className="text-sm font-medium text-foreground">
              {isUser ? "Vous" : "Odysseus"}
            </span>
            <span className="text-xs text-muted-foreground">{time}</span>
            {!isUser && message.content && <SpeakButton text={message.content} />}
            <MessageActions
              messageId={message.id}
              content={message.content}
              isUser={isUser}
            />
          </div>

          {/* Contenu — minimaliste : pas de bulle, texte en ligne */}
          <div
            className={cn(
              "text-sm leading-relaxed",
              isUser
                ? "rounded-2xl bg-surface-secondary border border-line-2 px-4 py-2 text-foreground"
                : "text-foreground"
            )}
          >
            <MarkdownContent content={message.content} />

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
    </div>
  );
}