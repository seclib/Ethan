"use client";

/**
 * ETHAN WebUI — ChatModeToggle : sélecteur discret du mode conversationnel
 * (Plan / Act / Debug) + effort de raisonnement, rendu dans le composer.
 *
 * La DÉCISION appartient entièrement au Core (core/chat/modes.py) : le mode
 * injecte ses instructions comportementales dans le prompt et sa matrice de
 * permissions filtre les outils proposés. Le WebUI envoie l'intent via le
 * payload chat (mode / reasoning_effort) et affiche l'état résolu — il ne
 * résout jamais lui-même une capacité.
 *
 * Volontairement discret (barre d'une ligne, badges colorés) pour ne pas
 * dupliquer le header (Agent/Model/Provider) — le mode est un réglage de la
 * conversation, pas une navigation.
 */

import * as React from "react";
import { Calendar, Zap, Bug, Gauge, SlidersHorizontal, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  CHAT_MODES,
  REASONING_EFFORTS,
  useChatModeStore,
  type ChatModeValue,
} from "@/store/chat-mode.store";

const MODE_ICONS: Record<ChatModeValue, typeof Zap> = {
  plan: Calendar,
  act: Zap,
  debug: Bug,
};

const MODE_ORDER: ChatModeValue[] = ["plan", "act", "debug"];

export function ChatModeToggle() {
  const mode = useChatModeStore((s) => s.mode);
  const setMode = useChatModeStore((s) => s.setMode);
  const reasoningEffort = useChatModeStore((s) => s.reasoningEffort);
  const setReasoningEffort = useChatModeStore((s) => s.setReasoningEffort);
  const [reasoningOpen, setReasoningOpen] = React.useState(false);

  return (
    <div className="flex items-center gap-1" role="group" aria-label="Mode conversationnel">
      {MODE_ORDER.map((key) => {
        const m = CHAT_MODES[key];
        const ModeIcon = MODE_ICONS[key];
        const active = key === mode;
        return (
          <button
            key={key}
            type="button"
            onClick={() => setMode(key)}
            aria-pressed={active}
            title={m.description}
            className={cn(
              "flex h-5 items-center gap-1 rounded-md px-1.5 text-[11px] font-medium",
              active
                ? cn("bg-accent/15 text-foreground", m.color)
                : "text-foreground-tertiary hover:bg-elevated hover:text-foreground-secondary"
            )}
          >
            <ModeIcon
              size={11}
              strokeWidth={2.5}
              className={active ? m.color : "text-foreground-tertiary"}
            />
            {m.label}
          </button>
        );
      })}

      <Popover open={reasoningOpen} onOpenChange={setReasoningOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-expanded={reasoningOpen}
            className="flex h-5 w-5 items-center justify-center rounded-md text-foreground-tertiary hover:bg-elevated hover:text-foreground-secondary"
            title={`Effort de raisonnement : ${reasoningEffort}`}
            aria-label="Effort de raisonnement"
          >
            <Gauge size={12} strokeWidth={2.5} />
          </button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-48 p-0">
          <div className="border-b border-line-1 px-2.5 py-1.5">
            <p className="text-[10px] font-medium uppercase tracking-wider text-foreground-tertiary">
              Reasoning
            </p>
          </div>
          <div className="p-1">
            {REASONING_EFFORTS.map(({ value, label }) => {
              const active = value === reasoningEffort;
              return (
                <button
                  key={value}
                  type="button"
                  role="radio"
                  aria-checked={active}
                  onClick={() => setReasoningEffort(value)}
                  className="flex w-full items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left text-xs text-foreground transition-colors hover:bg-elevated"
                >
                  <span className="flex items-center gap-1.5">
                    <SlidersHorizontal
                      size={12}
                      strokeWidth={2.5}
                      className={active ? "text-accent" : "text-foreground-tertiary"}
                    />
                    {label}
                  </span>
                  {active && <Check size={12} className="text-accent" />}
                </button>
              );
            })}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}