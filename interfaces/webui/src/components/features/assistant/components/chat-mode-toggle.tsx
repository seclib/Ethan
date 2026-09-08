"use client";

import { cn } from "@/lib/utils";
import { Zap, CircleDot, Bot } from "lucide-react";

export type ChatMode = "act" | "plan" | "agent";

interface ChatModeToggleProps {
  /** Mode courant du chat. */
  mode: ChatMode;
  /** Changement de mode. */
  onModeChange?: (mode: ChatMode) => void;
  /** État de désactivation (génération en cours). */
  disabled?: boolean;
}

/**
 * Toggle de mode chat — [Act | Plan | Agent].
 * Inspiré d'AnythingLLM : boutons segmentés, clic souris, touche Entrée pour valider.
 * Aucune logique métier — délègue onModeChange au parent.
 */
export function ChatModeToggle({ mode, onModeChange, disabled }: ChatModeToggleProps) {
  return (
    <div className="inline-flex items-center gap-0.5 rounded-lg border border-line-1 bg-bg-1 p-0.5 text-xs font-medium">
      <button
        type="button"
        onClick={() => onModeChange?.("act")}
        disabled={disabled}
        title="Act — Conversation directe"
        className={cn(
          "flex items-center gap-1 rounded-md px-2.5 py-1.5 transition-colors",
          mode === "act"
            ? "bg-accent/15 text-accent"
            : "text-foreground-secondary hover:bg-bg-3",
          disabled && "cursor-not-allowed opacity-50",
        )}
      >
        <Zap size={12} />
        <span className="hidden sm:inline">Act</span>
      </button>

      <button
        type="button"
        onClick={() => onModeChange?.("plan")}
        disabled={disabled}
        title="Plan — Planification de goal"
        className={cn(
          "flex items-center gap-1 rounded-md px-2.5 py-1.5 transition-colors",
          mode === "plan"
            ? "bg-accent/15 text-accent"
            : "text-foreground-secondary hover:bg-bg-3",
          disabled && "cursor-not-allowed opacity-50",
        )}
      >
        <CircleDot size={12} />
        <span className="hidden sm:inline">Plan</span>
      </button>

      <button
        type="button"
        onClick={() => onModeChange?.("agent")}
        disabled={disabled}
        title="Agent — Exécution autonome"
        className={cn(
          "flex items-center gap-1 rounded-md px-2.5 py-1.5 transition-colors",
          mode === "agent"
            ? "bg-accent/15 text-accent"
            : "text-foreground-secondary hover:bg-bg-3",
          disabled && "cursor-not-allowed opacity-50",
        )}
      >
        <Bot size={12} />
        <span className="hidden sm:inline">Agent</span>
      </button>
    </div>
  );
}

