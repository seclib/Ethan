"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ArrowDown, AlertCircle, X, Loader2 } from "lucide-react";
import type { AssistantMessage, SessionMetrics } from "@/types/assistant";
import { AssistantMessageView } from "./assistant-message";
import { AssistantInput } from "./assistant-input";
import { TypingIndicator } from "./typing-indicator";

/** Item de sélection d'une capacité dans le composer. */
export interface ComposerCapabilityItem {
  id: string;
  name: string;
  /** Badge optionnel (ex. provider d'un tool : builtin / mcp). */
  badge?: string;
}

interface AssistantChatProps {
  messages: AssistantMessage[];
  metrics: SessionMetrics;
  /** Identifiant de la conversation courante — déclenche le retour en bas au changement. */
  chatId?: string | null;
  /** Chargement d'un historique en cours. */
  isLoading?: boolean;
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  onFileAttached?: (fileId: string, filename: string) => void;
  /** Mode Plan : transmet au composer pour soumettre une intention comme goal. */
  onPlan?: (message: string) => void;
  /**
   * NOTE (dé-duplication) : les props capacités du composer (skills/collections/
   * tools/sélections/provider/model) ont été RETIRÉES — le composer simplifié
   * ne les rend plus. Les sélections actives vivent dans la page (payload chat)
   * et leur représentation visuelle est la ChatContextBar ; les sélecteurs
   * Agent/Model ont UNE position : le header (AssistantTopBar).
   */
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
  chatId,
  isLoading,
  onSend,
  onStop,
  disabled,
  onFileAttached,
  onPlan,
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
   * Changement de conversation (ouverture historique, refresh, nouvelle
   * conversation) : retour en bas immédiat et réactivation de l'auto-scroll.
   */
  useEffect(() => {
    autoScrollRef.current = true;
    setShowScrollDown(false);
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [chatId]);

  /**
   * Auto-scroll pendant la génération — uniquement si l'utilisateur
   * n'a pas remonté le fil. Double requestAnimationFrame : attend que le
   * markdown soit peint avant de mesurer scrollHeight (messages longs).
   */
  useEffect(() => {
    if (!autoScrollRef.current) return;
    let frame2 = 0;
    const frame1 = requestAnimationFrame(() => {
      frame2 = requestAnimationFrame(() =>
        scrollToBottom(disabled ? "auto" : "smooth"),
      );
    });
    return () => {
      cancelAnimationFrame(frame1);
      cancelAnimationFrame(frame2);
    };
  }, [messages, disabled, scrollToBottom]);

  // Dernier message assistant = celui en cours de génération pendant `disabled`.
  const lastAssistantId = [...messages].reverse().find((m) => m.role === "assistant")?.id;
  /**
   * En attente du premier token : génération active mais la réponse assistant
   * n'affiche encore aucun contenu — c'est le seul cas où l'indicateur de
   * frappe est affiché (sinon il ferait doublon avec le texte qui stream).
   */
  const lastAssistant = messages.find((m) => m.id === lastAssistantId);
  const waitingForFirstToken =
    !!disabled && (!lastAssistant || (!lastAssistant.content && !lastAssistant.done));

  return (
    <div className="relative flex-1 flex flex-col min-h-0">
      {/* Messages — wrapper relatif : le bouton « retour en bas » s'ancre à la
          SEULE zone des messages (et non au conteneur chat complet). Sinon son
          offset `bottom` fixe entre en collision avec le composer quand la
          textarea grandit (auto-resize jusqu'à 200px). */}
      <div className="relative flex-1 min-h-0">
        <div ref={scrollRef} onScroll={handleScroll} className="h-full overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6 space-y-6">
          {isLoading && (
            <div className="flex justify-center py-6" role="status" aria-label="Chargement de la conversation">
              <Loader2 size={20} className="animate-spin text-muted-foreground" />
            </div>
          )}
          {messages.length === 0 && !isLoading && (
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
          {waitingForFirstToken && <TypingIndicator />}
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
            className="absolute bottom-4 left-1/2 -translate-x-1/2 z-floating flex h-9 w-9 items-center justify-center rounded-full border border-line-2 bg-surface text-foreground-secondary shadow-lg hover:bg-bg-3 hover:text-foreground transition-colors"
            title="Retour en bas"
            aria-label="Retour en bas"
          >
            <ArrowDown size={16} />
          </button>
        )}
      </div>

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
        onPlan={onPlan}
      />
    </div>
  );
}
