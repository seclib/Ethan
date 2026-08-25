"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ArrowDown, AlertCircle, X } from "lucide-react";
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
  /** Erreur globale du flux (use-chats) — affichée en bannière non bloquante. */
  error?: string | null;
  onDismissError?: () => void;
  /** Régénère la réponse qui suit le dernier message utilisateur. */
  onRegenerate?: (assistantMessageId: string) => void;
  /** Édition d'un message utilisateur : renvoi du contenu modifié. */
  onEditMessage?: (messageId: string, newContent: string) => void;
}

/** Seuil (px) sous lequel on considère l'utilisateur « en bas » du fil. */
const BOTTOM_THRESHOLD = 80;

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
  error,
  onDismissError,
  onRegenerate,
  onEditMessage,
}: AssistantChatProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  // Ref (et non state) : lu dans les effets sans recréer de closures obsolètes.
  const autoScrollRef = useRef(true);
  const [showScrollDown, setShowScrollDown] = useState(false);

  /** L'utilisateur est-il en bas du fil ? */
  const isNearBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_THRESHOLD;
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior });
  }, []);

  /** Scroll utilisateur : s'il remonte, on coupe l'auto-scroll. */
  const handleScroll = useCallback(() => {
    const nearBottom = isNearBottom();
    autoScrollRef.current = nearBottom;
    setShowScrollDown(!nearBottom);
  }, [isNearBottom]);

  /**
   * Auto-scroll pendant la génération — uniquement si l'utilisateur
   * n'a pas remonté le fil (comportement corrigé).
   */
  useEffect(() => {
    if (autoScrollRef.current) {
      scrollToBottom(disabled ? "auto" : "smooth");
    }
  }, [messages, disabled, scrollToBottom]);

  // Dernier message assistant = celui en cours de génération pendant `disabled`.
  const lastAssistantId = [...messages].reverse().find((m) => m.role === "assistant")?.id;

  return (
    <div className="relative flex-1 flex flex-col min-h-0">
      {/* Messages */}
      <div ref={scrollRef} onScroll={handleScroll} className="flex-1 overflow-y-auto">
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
            <AssistantMessageView
              key={msg.id}
              message={msg}
              isStreaming={disabled && msg.id === lastAssistantId && !msg.done}
              onRegenerate={onRegenerate}
              onEditMessage={onEditMessage}
              editDisabled={disabled}
            />
          ))}
          {disabled && <TypingIndicator />}
          <div className="h-1" />
        </div>
      </div>

      {/* Bouton retour en bas — visible dès que l'utilisateur a remonté le fil */}
      {showScrollDown && (
        <button
          onClick={() => {
            autoScrollRef.current = true;
            setShowScrollDown(false);
            scrollToBottom("smooth");
          }}
          className="absolute bottom-[120px] left-1/2 -translate-x-1/2 z-10 flex h-9 w-9 items-center justify-center rounded-full border border-line-2 bg-surface text-foreground-secondary shadow-lg hover:bg-bg-3 hover:text-foreground transition-colors"
          title="Retour en bas"
          aria-label="Retour en bas"
        >
          <ArrowDown size={16} />
        </button>
      )}

      {/* Bannière d'erreur — non bloquante, dismissable */}
      {error && (
        <div className="mx-auto mb-1 flex w-full max-w-3xl items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
          <AlertCircle size={15} className="mt-0.5 shrink-0" />
          <span className="min-w-0 flex-1 break-words">{error}</span>
          {onDismissError && (
            <button
              onClick={onDismissError}
              className="shrink-0 rounded p-0.5 text-red-400/70 hover:bg-red-500/10 hover:text-red-400"
              title="Fermer"
              aria-label="Fermer l'erreur"
            >
              <X size={14} />
            </button>
          )}
        </div>
      )}

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
