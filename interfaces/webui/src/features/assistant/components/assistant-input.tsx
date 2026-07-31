"use client";

import { useState, useRef, KeyboardEvent } from "react";

interface AssistantInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function AssistantInput({ onSend, disabled }: AssistantInputProps) {
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

  return (
    <div className="border-t border-line-2 bg-background/40 p-4">
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <button className="p-2 text-muted-foreground hover:text-foreground transition-colors" title="Attacher un fichier">
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
            className="w-full bg-background/20 border border-line-1/20 rounded-lg px-4 py-2.5 text-sm text-foreground placeholder-muted-foreground resize-none focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
            style={{ minHeight: "42px", maxHeight: "200px" }}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="px-4 py-2.5 bg-accent hover:bg-accent/90 disabled:bg-line-1/20 disabled:text-muted-foreground text-foreground rounded-lg text-sm font-medium transition-colors"
        >
          ▶
        </button>
      </div>
    </div>
  );
}
