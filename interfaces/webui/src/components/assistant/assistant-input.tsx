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
    <div className="border-t border-gray-800 bg-gray-900/50 p-4">
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <button className="p-2 text-gray-400 hover:text-white transition-colors" title="Attacher un fichier">
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
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500 transition-colors disabled:opacity-50"
            style={{ minHeight: "42px", maxHeight: "200px" }}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          ▶
        </button>
      </div>
    </div>
  );
}