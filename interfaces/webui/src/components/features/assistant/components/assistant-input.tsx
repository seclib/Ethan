"use client";

import { useState, useRef, KeyboardEvent, type ChangeEvent, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import {
  Send,
  Square,
  Paperclip,
  Search,
  Wrench,
  Mic,
  X,
} from "lucide-react";


interface AssistantInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  /** File attachment handler (legacy : ouverture déléguée à la page) */
  onAttach?: () => void;
  /**
   * Fichiers choisis dans le picker natif. L'UPLOAD appartient à la page
   * propriétaire (Core : POST /files/upload) — l'input se contente d'ouvrir le
   * sélecteur natif et de remonter les fichiers. Prioritaire sur `onAttach`.
   */
  onFilesSelected?: (files: File[]) => void;
  /** Fichiers joints (état possédé par la page) — rendus dans le composer. */
  attachedFiles?: { id: string; name: string }[];
  /** Retrait d'un fichier joint (état possédé par la page). */
  onRemoveFile?: (id: string) => void;
  /** Search toggle handler */
  onSearch?: () => void;
  /** Tools toggle handler */
  onTools?: () => void;
  /** Voice input handler */
  onVoice?: () => void;
  /**
   * Slot Plugins (picker compact) — rendu dans les contrôles du composer.
   * Le contenu (état, catalogue, actions) appartient à la page propriétaire ;
   * l'input ne fait que l'exposer à sa place habituelle.
   */
  pluginsSlot?: ReactNode;
  /**
   * Slot Mode (ChatModeToggle) — rendu DANS la rangée d'actions du composer,
   * à la suite des contrôles fichiers/capacités (donc sur la même ligne que le
   * bouton `+`, comme la référence). Réglage de conversation (Plan/Act/Debug +
   * reasoning) possédé par la page via le store chat-mode ; l'input ne fait que
   * l'exposer à sa place.
   */
  modeSlot?: ReactNode;
}

export function AssistantInput({
  onSend,
  onStop,
  disabled,
  onAttach,
  onFilesSelected,
  attachedFiles,
  onRemoveFile,
  onSearch,
  onTools,
  onVoice,
  pluginsSlot,
  modeSlot,
}: AssistantInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /** Picker natif → remontée des fichiers à la page (upload Core côté page). */
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    // Reset : permet de re-sélectionner le MÊME fichier juste après.
    e.target.value = "";
    if (files.length > 0) onFilesSelected?.(files);
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

  const placeholder = "Message ETHAN...";

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
          {/* Fichiers joints (état page) — rendus au-dessus de la saisie, à
              proximité du bouton d'import de la rangée d'actions ci-dessous. */}
          {attachedFiles && attachedFiles.length > 0 && (
            <div className="flex flex-wrap items-center gap-1 px-1 pt-0.5">
              {attachedFiles.map((f) => (
                <span
                  key={f.id}
                  className="flex max-w-[220px] items-center gap-1 rounded-md border border-line-1 bg-bg-3 px-1.5 py-0.5 text-[11px] text-foreground-secondary"
                  title={f.name}
                >
                  <Paperclip size={10} className="shrink-0" />
                  <span className="truncate">{f.name}</span>
                  {onRemoveFile && (
                    <button
                      type="button"
                      onClick={() => onRemoveFile(f.id)}
                      className="shrink-0 rounded p-0.5 hover:text-foreground"
                      title={`Retirer ${f.name}`}
                      aria-label={`Retirer ${f.name}`}
                    >
                      <X size={10} />
                    </button>
                  )}
                </span>
              ))}
            </div>
          )}
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

          {/* Rangée d'actions du composer : fichiers/capacités à gauche, envoi à droite */}
          <div className="flex items-center justify-between gap-2">
            {/* Left: import de fichiers et capacités contextuelles (plugins, recherche, outils, voix) */}
            <div className="flex items-center gap-1">
              {pluginsSlot}
              {/* Import de fichiers : picker NATIF → upload réel par la page
                  (Core /files/upload). `onFilesSelected` prioritaire ;
                  `onAttach` conservé pour compatibilité. */}
              {onFilesSelected ? (
                <>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    aria-label="Joindre un fichier"
                    data-testid="chat-file-input"
                    onChange={handleFileChange}
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="flex h-7 w-7 items-center justify-center rounded-full text-foreground-secondary hover:bg-bg-3 hover:text-accent"
                    title="Attach file"
                  >
                    <Paperclip size={14} />
                  </button>
                </>
              ) : onAttach ? (
                <button
                  type="button"
                  onClick={onAttach}
                  className="flex h-7 w-7 items-center justify-center rounded-full text-foreground-secondary hover:bg-bg-3 hover:text-accent"
                  title="Attach file"
                >
                  <Paperclip size={14} />
                </button>
              ) : null}
              {onSearch && (
                <button
                  onClick={onSearch}
                  className="flex h-7 w-7 items-center justify-center rounded-full text-foreground-secondary hover:bg-bg-3 hover:text-accent"
                  title="Search"
                >
                  <Search size={14} />
                </button>
              )}
              {onTools && (
                <button
                  onClick={onTools}
                  className="flex h-7 w-7 items-center justify-center rounded-full text-foreground-secondary hover:bg-bg-3 hover:text-accent"
                  title="Tools"
                >
                  <Wrench size={14} />
                </button>
              )}
              {onVoice && (
                <button
                  onClick={onVoice}
                  className="flex h-7 w-7 items-center justify-center rounded-full text-foreground-secondary hover:bg-bg-3 hover:text-accent"
                  title="Voice input"
                >
                  <Mic size={14} />
                </button>
              )}
              {/* Plan / Act / Debug + effort de raisonnement — MÊME rangée que
                  les contrôles (fichiers/plugins), à droite du bouton `+` :
                  un seul pavé de commandes sous la saisie (référence). */}
              {modeSlot ? <div className="flex items-center gap-1">{modeSlot}</div> : null}
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
