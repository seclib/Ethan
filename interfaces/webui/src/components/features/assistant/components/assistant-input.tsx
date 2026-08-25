"use client";

import { useState, useRef, KeyboardEvent, useEffect } from "react";
import { useUIStore } from "@/store/ui.store";
import { cn } from "@/lib/utils";
import { uploadFile } from "@/lib/api/files";
import { Paperclip, Send, Square, X, Plus, Wrench, Bot, Database } from "lucide-react";

interface AssistantInputProps {
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
}

export function AssistantInput({
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
}: AssistantInputProps) {
  const [message, setMessage] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const addToast = useUIStore((s) => s.addToast);
  const [attachments, setAttachments] = useState<{ id: string; name: string }[]>([]);
  const [uploading, setUploading] = useState(false);

  // Close menu on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setUploading(true);
    try {
      for (const file of files) {
        const record = await uploadFile(file);
        setAttachments((prev) => [...prev, { id: record.id, name: record.filename }]);
        onFileAttached?.(record.id, record.filename);
      }
      addToast({ type: "success", message: `${files.length} fichier(s) attaché(s)` });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Upload failed" });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setMessage("");
    setAttachments([]);
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
    <div className="px-4 pb-4">
      <div className="mx-auto max-w-3xl">
        {/* Attachments strip */}
        {attachments.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {attachments.map((att) => (
              <div
                key={att.id}
                className="flex items-center gap-2 rounded-full border border-line-2 bg-bg-2 px-3 py-1 text-xs text-foreground-secondary"
              >
                <Paperclip size={12} className="text-foreground-tertiary" />
                <span className="max-w-[200px] truncate">{att.name}</span>
                <button
                  onClick={() => removeAttachment(att.id)}
                  className="text-foreground-tertiary hover:text-foreground"
                  title="Retirer"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Active toggles indicator */}
        {(toolsEnabled || agentEnabled || knowledgeEnabled) && (
          <div className="mb-2 flex flex-wrap gap-2">
            {toolsEnabled && (
              <span className="flex items-center gap-1 rounded-full bg-accent/10 px-2.5 py-0.5 text-[11px] text-accent">
                <Wrench size={11} /> Outils
              </span>
            )}
            {agentEnabled && (
              <span className="flex items-center gap-1 rounded-full bg-accent/10 px-2.5 py-0.5 text-[11px] text-accent">
                <Bot size={11} /> Agent
              </span>
            )}
            {knowledgeEnabled && (
              <span className="flex items-center gap-1 rounded-full bg-accent/10 px-2.5 py-0.5 text-[11px] text-accent">
                <Database size={11} /> Knowledge
              </span>
            )}
          </div>
        )}

        <div
          className={cn(
            "chat-input-bar",
            "focus-within:border-accent/60"
          )}
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Message..."
            rows={1}
            disabled={disabled}
            className="w-full resize-none bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
            style={{ minHeight: "40px", maxHeight: "200px" }}
          />

          <div className="flex items-center justify-between px-2 pb-1">
            {/* Left: options menu */}
            <div className="flex items-center gap-1">
              {!disabled && (
                <>
                  <div className="relative" ref={menuRef}>
                    <button
                      onClick={() => setMenuOpen(!menuOpen)}
                      className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-full transition-colors",
                        menuOpen ? "bg-accent/15 text-accent" : "text-muted-foreground hover:text-foreground hover:bg-surface-secondary"
                      )}
                      title="Options"
                    >
                      <Plus size={16} />
                    </button>

                    {menuOpen && (
                      <div className="absolute bottom-10 left-0 z-50 w-56 rounded-xl border border-line-2 bg-surface p-1.5 shadow-xl">
                        <button
                          onClick={() => { fileInputRef.current?.click(); setMenuOpen(false); }}
                          className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground-secondary hover:bg-bg-3 hover:text-foreground"
                        >
                          <Paperclip size={15} />
                          <span>Fichiers</span>
                        </button>
                        <button
                          onClick={() => { onToggleTools?.(); setMenuOpen(false); }}
                          className={cn(
                            "flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm hover:bg-bg-3",
                            toolsEnabled ? "text-accent" : "text-foreground-secondary hover:text-foreground"
                          )}
                        >
                          <Wrench size={15} />
                          <span>Outils</span>
                          {toolsEnabled && <span className="ml-auto text-[10px] text-accent">●</span>}
                        </button>
                        <button
                          onClick={() => { onToggleAgent?.(); setMenuOpen(false); }}
                          className={cn(
                            "flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm hover:bg-bg-3",
                            agentEnabled ? "text-accent" : "text-foreground-secondary hover:text-foreground"
                          )}
                        >
                          <Bot size={15} />
                          <span>Agent</span>
                          {agentEnabled && <span className="ml-auto text-[10px] text-accent">●</span>}
                        </button>
                        <button
                          onClick={() => { onToggleKnowledge?.(); setMenuOpen(false); }}
                          className={cn(
                            "flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm hover:bg-bg-3",
                            knowledgeEnabled ? "text-accent" : "text-foreground-secondary hover:text-foreground"
                          )}
                        >
                          <Database size={15} />
                          <span>Knowledge</span>
                          {knowledgeEnabled && <span className="ml-auto text-[10px] text-accent">●</span>}
                        </button>
                      </div>
                    )}
                  </div>

                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={handleFileSelect}
                  />
                </>
              )}
            </div>

            {/* Right: send/stop */}
            <div className="flex items-center gap-1">
              {!disabled && (
                <span className="text-[10px] text-muted-foreground/60 mr-1">
                  Shift + Entrée
                </span>
              )}
              {isGenerating ? (
                <button
                  onClick={() => onStop?.()}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-red-500/90 hover:bg-red-500 text-white transition-colors"
                  title="Arrêter la génération"
                >
                  <Square size={14} fill="currentColor" />
                </button>
              ) : (
                <button
                  onClick={handleSend}
                  disabled={disabled || !message.trim()}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-white hover:bg-accent/90 disabled:bg-line-2 disabled:text-muted-foreground transition-colors"
                  title="Envoyer"
                >
                  <Send size={14} />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}