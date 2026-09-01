"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { cn } from "@/lib/utils";
import {
  Send,
  Square,
} from "lucide-react";

/**
 * NOTE (dé-duplication) : le composer n'expose PAS de sélecteur d'agent —
 * le sélecteur d'agent a UNE position principale : le header du chat
 * (AgentSelector, cf. assistant-top-bar). Même règle que la ChatContextBar :
 * les chips/dropdowns Agent et Model ont été retirés d'ici. Les props
 * agents/selectedAgentId/… ne sont plus acceptées.
 */
interface AssistantInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  onFileAttached?: (fileId: string, filename: string) => void;
  onOpenModelSelector?: () => void;
  /** Mode Plan : soumet l'intention comme un goal réel (API /v1/goals). */
  onPlan?: (message: string) => void;
}

export function AssistantInput({
  onSend,
  onStop,
  disabled,
  onPlan,
}: AssistantInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setMessage("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter en cours de composition IME (jp/zh/ko) ne doit jamais envoyer.
    if (e.key !== "Enter" || e.nativeEvent.isComposing) return;
    if (e.shiftKey) return; // nouvelle ligne : comportement natif
    e.preventDefault();
    handleSend();
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }
  };

  const isGenerating = disabled && !!onStop;

  const handlePlan = () => {
    const trimmed = message.trim();
    if (!trimmed || disabled || !onPlan) return;
    onPlan(trimmed);
    setMessage("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  return (
    <div
      className="px-4 pt-2"
      style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
    >
      <div className="mx-auto max-w-3xl">
        {/* Composer bar — structure simple : saisie au-dessus, contrôles en dessous */}
        <div
          className={cn(
            "flex flex-col gap-1 rounded-2xl border border-line-1 bg-bg-1 px-3 py-2",
            "focus-within:border-accent/60",
          )}
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Message ETHAN..."
            rows={1}
            disabled={disabled}
            className="min-h-[40px] w-full resize-none border-0 bg-transparent px-1 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none disabled:opacity-50"
            style={{ maxHeight: "200px" }}
          />

          <div className="flex items-center justify-between gap-2">
            {/* Left : modes Act / Plan — seuls contrôles visibles */}
            <div className="flex items-center gap-1">
              {/* Act = mode standard réel : envoi direct vers le Core (défaut). */}
              <button
                className="flex h-7 items-center rounded-full bg-accent/15 px-2.5 text-xs font-medium text-accent"
                title="Mode standard — ETHAN répond directement"
                aria-pressed="true"
              >
                <span className="hidden sm:inline">Act</span>
                <span className="sm:hidden">A</span>
              </button>
              {/* Plan : soumet l'intention comme un goal (API /v1/goals réelle,
                  gérée par le Core). Le bouton est actif quand la saisie n'est
                  pas vide et qu'un gestionnaire est fourni. */}
              <button
                onClick={handlePlan}
                disabled={disabled || !message.trim() || !onPlan}
                className="flex h-7 items-center rounded-full px-2.5 text-xs font-medium text-accent/90 hover:bg-accent/15 disabled:cursor-not-allowed disabled:text-foreground-tertiary disabled:opacity-50"
                title="Créer un objectif (goal) à partir de cette intention — planification gérée par ETHAN Core"
                aria-pressed="false"
              >
                <span className="hidden sm:inline">Plan</span>
                <span className="sm:hidden">P</span>
              </button>
            </div>

            {/* Right : send / stop — toujours visible */}
            {isGenerating ? (
              <button
                onClick={() => onStop?.()}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-red-500/90 hover:bg-red-500 text-white transition-colors"
                title="Arrêter la génération"
                aria-label="Arrêter la génération"
              >
                <Square size={14} fill="currentColor" />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={disabled || !message.trim()}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-white shadow-sm hover:bg-accent/90 disabled:bg-line-2 disabled:text-muted-foreground transition-colors"
                title="Envoyer (Entrée)"
                aria-label="Envoyer le message"
              >
                <Send size={15} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
