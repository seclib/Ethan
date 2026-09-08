"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { cn } from "@/lib/utils";
import {
  Send,
  Square,
  Paperclip,
  Search,
  Wrench,
  Mic,
  Bot,
  Zap,
  CircleDot,
} from "lucide-react";

export type ChatMode = "act" | "plan" | "agent";

interface AssistantInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  /** Mode Plan : soumet l'intention comme un goal réel (API /v1/goals). */
  onPlan?: (message: string) => void;
  /** Mode Agent : envoie la tâche à un agent autonome. */
  onAgent?: (message: string) => void;
  /** Current mode */
  mode?: ChatMode;
  /** Mode change handler */
  onModeChange?: (mode: ChatMode) => void;
  /** File attachment handler */
  onAttach?: () => void;
  /** Search toggle handler */
  onSearch?: () => void;
  /** Tools toggle handler */
  onTools?: () => void;
  /** Voice input handler */
  onVoice?: () => void;
}

export function AssistantInput({
  onSend,
  onStop,
  disabled,
  onPlan,
  onAgent,
  mode = "act",
  onModeChange,
  onAttach,
  onSearch,
  onTools,
  onVoice,
}: AssistantInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || disabled) return;

    switch (mode) {
      case "agent":
        onAgent?.(trimmed);
        break;
      case "plan":
        onPlan?.(trimmed);
        break;
      default:
        onSend(trimmed);
    }
    setMessage("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== "Enter" || e.nativeEvent.isComposing) return;
    if (e.shiftKey) return;
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

  const placeholder =
    mode === "agent"
      ? "Describe a task for the agent..."
      : mode === "plan"
        ? "Describe a goal to plan..."
        : "Message ETHAN...";

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
            placeholder={placeholder}
            rows={1}
            disabled={disabled}
            className="min-h-[40px] w-full resize-none border-0 bg-transparent px-1 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none disabled:opacity-50"
            style={{ maxHeight: "200px" }}
          />

          <div className="flex items-center justify-between gap-2">
            {/* Left: modes + contextual capabilities */}
            <div className="flex items-center gap-1">
              {/* Mode selector */}
              <button
                onClick={() => onModeChange?.("act")}
                className={cn(
                  "flex h-7 items-center rounded-full px-2.5 text-xs font-medium transition-colors",
                  mode === "act"
                    ? "bg-accent/15 text-accent"
                    : "text-foreground-secondary hover:bg-accent/10",
                )}
                title="Act — ETHAN responds directly"
              >
                <Zap size={12} className="mr-1" />
                <span className="hidden sm:inline">Act</span>
              </button>
              <button
                onClick={() => onModeChange?.("plan")}
                className={cn(
                  "flex h-7 items-center rounded-full px-2.5 text-xs font-medium transition-colors",
                  mode === "plan"
                    ? "bg-accent/15 text-accent"
                    : "text-foreground-secondary hover:bg-accent/10",
                )}
                title="Plan — Create a goal"
              >
                <CircleDot size={12} className="mr-1" />
                <span className="hidden sm:inline">Plan</span>
              </button>
              <button
                onClick={() => onModeChange?.("agent")}
                className={cn(
                  "flex h-7 items-center rounded-full px-2.5 text-xs font-medium transition-colors",
                  mode === "agent"
                    ? "bg-accent/15 text-accent"
                    : "text-foreground-secondary hover:bg-accent/10",
                )}
                title="Agent — Autonomous task execution"
              >
                <Bot size={12} className="mr-1" />
                <span className="hidden sm:inline">Agent</span>
              </button>

              <div className="mx-1 h-4 w-px bg-line-1" />

              {/* Contextual capabilities */}
              {onAttach && (
                <button
                  onClick={onAttach}
                  className="flex h-7 w-7 items-center justify-center rounded-full text-foreground-secondary hover:bg-accent/10 hover:text-accent"
                  title="Attach file"
                >
                  <Paperclip size={14} />
                </button>
              )}
              {onSearch && (
                <button
                  onClick={onSearch}
                  className="flex h-7 w-7 items-center justify-center rounded-full text-foreground-secondary hover:bg-accent/10 hover:text-accent"
                  title="Search"
                >
                  <Search size={14} />
                </button>
              )}
              {onTools && (
                <button
                  onClick={onTools}
                  className="flex h-7 w-7 items-center justify-center rounded-full text-foreground-secondary hover:bg-accent/10 hover:text-accent"
                  title="Tools"
                >
                  <Wrench size={14} />
                </button>
              )}
              {onVoice && (
                <button
                  onClick={onVoice}
                  className="flex h-7 w-7 items-center justify-center rounded-full text-foreground-secondary hover:bg-accent/10 hover:text-accent"
                  title="Voice input"
                >
                  <Mic size={14} />
                </button>
              )}
            </div>

            {/* Right: send / stop */}
            {isGenerating ? (
              <button
                onClick={() => onStop?.()}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-red-500/90 hover:bg-red-500 text-white transition-colors"
                title="Stop generation"
                aria-label="Stop generation"
              >
                <Square size={14} fill="currentColor" />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={disabled || !message.trim()}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-white shadow-sm hover:bg-accent/90 disabled:bg-line-2 disabled:text-muted-foreground transition-colors"
                title="Send (Enter)"
                aria-label="Send message"
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
