"use client";

import { useState, useRef, KeyboardEvent, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Send,
  Square,
  Bot,
  Check,
  ChevronDown,
  Plus,
} from "lucide-react";
import type { ComposerCapabilityItem } from "./assistant-chat";

/**
 * Props conservées pour compatibilité d'appel (assistant-chat passe encore
 * skills/collections/tools/… mais le composer simplifié ne les rend plus) :
 * les capacités restent accessibles via leurs pages dédiées et l'API.
 */
interface AssistantInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  onFileAttached?: (fileId: string, filename: string) => void;
  /** Catalogues de capacités (source : Core) sélectionnables dans le composer. */
  skills?: ComposerCapabilityItem[];
  collections?: ComposerCapabilityItem[];
  tools?: ComposerCapabilityItem[];
  agents?: ComposerCapabilityItem[];
  /** Sélections actives (Open-WebUI style : cocher des items). */
  selectedSkillIds?: string[];
  selectedCollectionIds?: string[];
  selectedToolIds?: string[];
  selectedAgentId?: string | null;
  selectedAgentName?: string;
  /** Provider/model actifs — pour l'affichage dans le composer. */
  activeProvider?: string;
  activeModel?: string;
  onToggleSkill?: (id: string) => void;
  onToggleCollection?: (id: string) => void;
  onToggleTool?: (id: string) => void;
  onSelectAgent?: (id: string | null) => void;
  onOpenModelSelector?: () => void;
}

function AgentDropdown({
  agents,
  selectedId,
  selectedName,
  onSelect,
  disabled,
}: {
  agents: ComposerCapabilityItem[];
  selectedId: string | null;
  selectedName?: string;
  onSelect: (id: string | null) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const selected = selectedName || "Agent";

  return (
    <div ref={wrapRef} className="relative inline-flex">
      <button
        onClick={() => setOpen((o) => !o)}
        disabled={disabled}
        className={cn(
          "flex h-7 items-center gap-1.5 rounded-full px-2.5 text-xs transition-colors",
          open
            ? "bg-accent/15 text-accent"
            : "text-foreground-tertiary hover:bg-surface-secondary hover:text-foreground",
          disabled && "pointer-events-none opacity-40",
        )}
        title="Changer d'agent"
      >
        <Bot size={14} />
        <span className="hidden sm:inline">{selected}</span>
        <ChevronDown size={12} />
      </button>
      {open && (
        <div className="absolute bottom-11 left-0 z-50 w-56 rounded-xl border border-line-2 bg-surface p-1 shadow-xl">
          <div className="max-h-64 overflow-y-auto">
            <button
              className={cn(
                "flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm",
                !selectedId ? "bg-accent/10 text-accent" : "text-foreground-secondary hover:bg-bg-3",
              )}
              onClick={() => { onSelect(null); setOpen(false); }}
            >
              <span className="flex h-3.5 w-3.5 items-center justify-center">
                <div className="h-2.5 w-2.5 rounded-full bg-accent/40" />
              </span>
              <span>Sans agent</span>
            </button>
            {agents.map((agent) => {
              const active = selectedId === agent.id;
              return (
                <button
                  key={agent.id}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm",
                    active ? "bg-accent/10 text-accent" : "text-foreground-secondary hover:bg-bg-3",
                  )}
                  onClick={() => { onSelect(agent.id); setOpen(false); }}
                >
                  <Bot size={14} />
                  <span className="truncate">{agent.name}</span>
                  {active && <Check size={11} className="ml-auto text-accent" />}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => { window.location.href = "/agents"; }}
            className="flex w-full items-center justify-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-foreground-tertiary hover:bg-bg-3"
          >
            <Plus size={12} />
            Créer/Configurer un agent
          </button>
        </div>
      )}
    </div>
  );
}

export function AssistantInput({
  onSend,
  onStop,
  disabled,
  agents,
  selectedAgentId,
  selectedAgentName,
  onSelectAgent,
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
    <div className="border-t border-line-1 bg-bg-2/50 px-4 py-3">
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
            {/* Left : modes Act / Plan / Agent — seuls contrôles visibles */}
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
              {/* Plan : la planification est gérée automatiquement par le Core
                  (module planner, routage d'intention). Aucun paramètre « mode »
                  n'est exposé par l'API chat — contrôle volontairement désactivé,
                  pas simulé. Cf. docs/plans/chat-composer-simplification.md */}
              <button
                disabled
                aria-disabled="true"
                className="flex h-7 cursor-not-allowed items-center rounded-full px-2.5 text-xs text-foreground-tertiary opacity-50"
                title="Planification gérée automatiquement par le Core — sélection manuelle non encore disponible"
              >
                <span className="hidden sm:inline">Plan</span>
                <span className="sm:hidden">P</span>
              </button>
              {/* Agent : sélection réelle (agent_id envoyé au Core) */}
              {agents && agents.length > 0 && (
                <AgentDropdown
                  agents={agents}
                  selectedId={selectedAgentId ?? null}
                  selectedName={selectedAgentName}
                  onSelect={onSelectAgent ?? (() => {})}
                  disabled={disabled}
                />
              )}
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
