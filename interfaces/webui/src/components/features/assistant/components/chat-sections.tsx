"use client";

/**
 * ETHAN WebUI — ChatSections : navigation par catégories d'usage du Chat
 * (Code / Apprendre / Créer / Écrire / Vie quotidienne).
 *
 * Position : rendue par la page chat SOUS le composer (parité avec l'image de
 * référence — les catégories sont juste sous la carte de saisie).
 *
 * UI-only — aucune logique métier. La conversation reste unique ; la section
 * active agit comme un contexte UX/filter. Extensible via useChatSectionStore.
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Code,
  BookOpen,
  Palette,
  PenLine,
  Coffee,
  type LucideIcon,
} from "lucide-react";
import {
  CHAT_SECTIONS,
  type ChatSectionId,
  useChatSectionStore,
} from "@/store/chat-section.store";

const SECTION_ICONS: Record<ChatSectionId, LucideIcon> = {
  code: Code,
  learn: BookOpen,
  create: Palette,
  write: PenLine,
  daily: Coffee,
};

interface ChatSectionsProps {
  className?: string;
  /**
   * `bar` (défaut) : barre pleine largeur ancrée sous le composer, utilisée
   * pendant une conversation active.
   * `floating` : chips centrés sans fond ni bordure, utilisés dans l'état vide
   * (hero) — parité avec la référence où les catégories flottent sous la carte
   * de saisie. Présentation uniquement.
   */
  variant?: "bar" | "floating";
}

export function ChatSections({ className, variant = "bar" }: ChatSectionsProps) {
  const active = useChatSectionStore((s) => s.activeSection);
  const setSection = useChatSectionStore((s) => s.setSection);

  const isFloating = variant === "floating";

  return (
    <div
      className={cn(
        "shrink-0",
        isFloating ? "" : "border-t border-line-1 bg-background",
        className,
      )}
    >
      {/* Aligné sur la largeur de la conversation (max-w-3xl) et du composer. */}
      <nav
        className={cn(
          "mx-auto flex w-full max-w-3xl items-center gap-1 overflow-x-auto overflow-y-hidden px-4",
          isFloating ? "justify-center py-0" : "py-1.5",
        )}
        aria-label="Sections d'utilisation"
      >
        {CHAT_SECTIONS.map((section) => {
          const Icon = SECTION_ICONS[section.id];
          const isActive = section.id === active;
          return (
            <button
              key={section.id}
              type="button"
              aria-pressed={isActive}
              onClick={() => setSection(section.id)}
              className={cn(
                "flex h-7 items-center gap-1.5 rounded-md px-2.5 text-xs font-medium whitespace-nowrap transition-colors",
                isActive
                  ? "bg-bg-3 text-accent"
                  : "text-foreground-tertiary hover:bg-bg-3 hover:text-foreground-secondary"
              )}
              title={`Section : ${section.label.toLowerCase()}`}
            >
              <Icon className="h-3 w-3" strokeWidth={2.5} />
              <span>{section.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
