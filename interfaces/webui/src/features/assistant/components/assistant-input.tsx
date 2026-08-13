"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { useUIStore } from "@/core/store/ui.store";

interface AssistantInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
}

export function AssistantInput({ onSend, onStop, disabled }: AssistantInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const addToast = useUIStore((s) => s.addToast);

  const notImplemented = () => {
    addToast({ type: "info", message: "Feature not implemented yet" });
  };

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
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }
  };

  const isGenerating = disabled && !!onStop;

  return (
    <div className="border-t border-line-2 bg-background/40 p-4">
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <button
          onClick={notImplemented}
          disabled={disabled}
          className="p-2 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          title="Attacher un fichier"
        >
          📎
        </button>
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Envoyer un message..."
            rows={1}
            disabled={disabled}
            className="w-full bg-background/20 border border-line-1/20 rounded-lg px-4 py-2.5 pr-10 text-sm text-foreground placeholder-muted-foreground resize-none focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
            style={{ minHeight: "42px", maxHeight: "200px" }}
          />
          {/* Indicateur Shift+Entrée */}
          {!disabled && (
            <span className="absolute bottom-1.5 right-3 text-[10px] text-muted-foreground/60 pointer-events-none">
              ⏎ Entrée
            </span>
          )}
        </div>

        {/* Bouton Stop pendant la génération */}
        {isGenerating ? (
          <button
            onClick={() => onStop?.()}
            className="px-4 py-2.5 bg-red-500/90 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            title="Arrêter la génération"
          >
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
              <rect x="6" y="6" width="8" height="8" rx="1" />
            </svg>
            Stop
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={disabled || !message.trim()}
            className="px-4 py-2.5 bg-accent hover:bg-accent/90 disabled:bg-line-1/20 disabled:text-muted-foreground text-foreground rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <svg
              className="h-4 w-4"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11H6a1 1 0 00-1-1H3a1 1 0 000 2h1v1.571a3 3 0 002.618 2.97l5 1.429a1 1 0 001.169-1.409l-7-14zM13 7a1 1 0 10-2 0v2a1 1 0 102 0V7z" />
            </svg>
            Envoyer
          </button>
        )}
      </div>
    </div>
  );
}