"use client";

/**
 * ETHAN WebUI — ChatContextBar : représentation du contexte actif du chat.
 *
 * Répond en une seconde à la question « pourquoi ETHAN répond comme ça ? » :
 * Agent · Modèle · Tools · Skills · Knowledge · Mémoire.
 *
 * RÈGLE ANTI-FANTÔME (archi §chat-context) : cette barre n'affiche QUE des
 * capacités réellement actives, résolues par la page propriétaire depuis les
 * catalogues Core (GET /skills, /knowledge collections, /tools, /agents,
 * /memory facts). Une capacité dont l'identifiant ne se résout pas dans un
 * catalogue chargé est silencieusement exclue — jamais de chip inventé.
 *
 * Données en entrée : TOUS les items sont pré-résolus {id, name} par la page
 * (union agent ∪ sélection composer — même fusion que core/chat/pipeline.py,
 * recalculée pour AFFICHAGE uniquement). Aucune logique métier ici, aucune
 * requête réseau : composant purement présentationnel et réutilisable.
 */

import * as React from "react";
import { Brain, ChevronDown, Database, ExternalLink, Sparkles, Wrench } from "lucide-react";

export type ContextKind = "tool" | "skill" | "knowledge";

/** Item de capacité PRÉ-RÉSOLU (nom réel issu du catalogue Core). */
export interface ChatContextItem {
  id: string;
  name: string;
  /** Précision optionnelle : "builtin"/"mcp" pour un tool, défauts… */
  detail?: string;
}

export interface ChatContextBarProps {
  /**
   * NOTE (dé-duplication) : les chips Agent et Model ont été RETIRÉES de cette
   * barre — ces sélecteurs ont UNE position principale : le header du chat
   * (AgentSelector / ModelSelector). Cette barre n'expose plus que le contexte
   * de capacités actives (tools/skills/knowledge/mémoire), absent du header.
   */

  /** Capacités actives PRÉ-RÉSOLUES (union agent ∪ sélection composer). */
  tools?: ChatContextItem[];
  skills?: ChatContextItem[];
  knowledge?: ChatContextItem[];
  /** Clic sur un lien de page dédiée depuis un panneau de détail. */
  onCapabilityPageClick?: (kind: ContextKind) => void;

  /** Nombre de facts mémoire — chip rendu SEULEMENT si > 0. */
  memoryFactCount?: number | null;
  onMemoryClick?: () => void;

  className?: string;
}

type Panel = Exclude<ContextKind, never>;

/* ── Chip de base ──────────────────────────────────────────────────────────── */

interface ChipProps {
  icon: React.ReactNode;
  label: React.ReactNode;
  title: string;
  onClick?: () => void;
  expanded?: boolean;
  children?: React.ReactNode;
}

function ContextChip({ icon, label, title, onClick, expanded, children }: ChipProps) {
  const interactive = !!onClick;
  return (
    <div className="relative">
      <button
        type="button"
        onClick={onClick}
        disabled={!interactive}
        title={title}
        aria-expanded={interactive ? expanded : undefined}
        className={
          interactive
            ? "inline-flex h-7 max-w-[220px] items-center gap-1.5 rounded-md px-2 text-xs text-foreground-secondary transition-colors hover:bg-bg-3 hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
            : "inline-flex h-7 max-w-[220px] cursor-default items-center gap-1.5 rounded-md px-2 text-xs text-foreground-tertiary"
        }
      >
        {icon}
        <span className="truncate">{label}</span>
        {children}
      </button>
    </div>
  );
}

/* ── Panneau de détail capacités (popover léger) ──────────────────────────── */

const PANEL_META: Record<Panel, { title: string; pageLabel: string }> = {
  tool: { title: "Outils actifs", pageLabel: "Gérer les outils" },
  skill: { title: "Skills actives", pageLabel: "Gérer les skills" },
  knowledge: { title: "Connaissances sources", pageLabel: "Gérer les connaissances" },
};

function CapabilityPanel({
  kind,
  items,
  onPageClick,
  onClose,
}: {
  kind: Panel;
  items: ChatContextItem[];
  onPageClick?: (k: ContextKind) => void;
  onClose: () => void;
}) {
  const meta = PANEL_META[kind];
  return (
    <div className="absolute left-0 top-8 z-30 w-72 rounded-lg border border-line-1 bg-panel p-1.5 shadow-lg">
      <p className="px-2 py-1 text-[11px] font-medium uppercase tracking-wide text-foreground-tertiary">
        {meta.title}
      </p>
      <div className="custom-scrollbar max-h-52 overflow-y-auto">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-foreground-secondary"
          >
            <span className="truncate">{item.name}</span>
            {item.detail && (
              <span className="ml-auto shrink-0 rounded bg-elevated px-1.5 text-[10px] uppercase text-foreground-tertiary">
                {item.detail}
              </span>
            )}
          </div>
        ))}
      </div>
      {onPageClick && (
        <button
          type="button"
          onClick={() => {
            onClose();
            onPageClick(kind);
          }}
          className="mt-1 flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-xs text-accent transition-colors hover:bg-bg-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
        >
          <ExternalLink className="h-3 w-3" />
          {meta.pageLabel}
        </button>
      )}
    </div>
  );
}

/* ── Chip capacité avec panneau déroulant ─────────────────────────────────── */

const CAP_CHIP_META = {
  tool: { short: "outils", title: "Outils actifs", icon: Wrench },
  skill: { short: "skills", title: "Skills actives", icon: Sparkles },
  knowledge: { short: "sources", title: "Connaissances sources", icon: Database },
} as const;

function PanelChip({
  kind,
  items,
  panel,
  setPanel,
  onPageClick,
}: {
  kind: Panel;
  items: ChatContextItem[];
  panel: Panel | null;
  setPanel: (p: Panel | null) => void;
  onPageClick?: (k: ContextKind) => void;
}) {
  const meta = CAP_CHIP_META[kind];
  const Icon = meta.icon;
  const open = panel === kind;
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setPanel(open ? null : kind)}
        aria-expanded={open}
        title={`${meta.title} (${items.length})`}
        className="inline-flex h-7 max-w-[220px] items-center gap-1.5 rounded-md px-2 text-xs text-foreground-secondary transition-colors hover:bg-bg-3 hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
      >
        <Icon className="h-3.5 w-3.5 text-accent" />
        <span className="truncate">
          {items.length}&nbsp;&nbsp;{meta.short}
        </span>
        <ChevronDown className={`h-3 w-3 shrink-0 transition-transform ${open ? "rotate-180" : ""} opacity-60`} />
      </button>
      {open && (
        <CapabilityPanel kind={kind} items={items} onPageClick={onPageClick} onClose={() => setPanel(null)} />
      )}
    </div>
  );
}

/* ── Composant principal ──────────────────────────────────────────────────── */

export function ChatContextBar({
  tools = [],
  skills = [],
  knowledge = [],
  onCapabilityPageClick,
  memoryFactCount,
  onMemoryClick,
  className = "",
}: ChatContextBarProps) {
  const [panel, setPanel] = React.useState<Panel | null>(null);
  const rootRef = React.useRef<HTMLDivElement | null>(null);

  // Fermeture Échap / clic extérieur d'un panneau ouvert.
  React.useEffect(() => {
    if (!panel) return;
    const onDocMouseDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setPanel(null);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPanel(null);
    };
    document.addEventListener("mousedown", onDocMouseDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [panel]);

  // Règle anti-fantôme : la barre n'est rendue que s'il existe AU MOINS une
  // capacité réelle à montrer (jamais une ligne décorative vide).
  const hasContent =
    tools.length > 0 ||
    skills.length > 0 ||
    knowledge.length > 0 ||
    (!!memoryFactCount && memoryFactCount > 0);
  if (!hasContent) return null;

  return (
    <div
      ref={rootRef}
      aria-label="Contexte actif du chat"
      className={`flex flex-wrap items-center gap-0.5 border-b border-line-1/40 px-4 py-1 ${className}`}
    >
      {tools.length > 0 && (
        <PanelChip kind="tool" items={tools} panel={panel} setPanel={setPanel} onPageClick={onCapabilityPageClick} />
      )}
      {skills.length > 0 && (
        <PanelChip kind="skill" items={skills} panel={panel} setPanel={setPanel} onPageClick={onCapabilityPageClick} />
      )}
      {knowledge.length > 0 && (
        <PanelChip kind="knowledge" items={knowledge} panel={panel} setPanel={setPanel} onPageClick={onCapabilityPageClick} />
      )}

      {!!memoryFactCount && memoryFactCount > 0 && (
        <ContextChip
          icon={<Brain className="h-3.5 w-3.5 text-accent" />}
          label={`Mémoire · ${memoryFactCount}`}
          title={`Mémoire ETHAN active — ${memoryFactCount} fait(s) injectés par le pipeline`}
          onClick={onMemoryClick}
        />
      )}
    </div>
  );
}


