"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Bot, ChevronDown, Plus, Search } from "lucide-react";
import type { Agent } from "@/types";

interface AgentSelectorProps {
  /** Catalogue réel issu du Core (GET /v1/agents via useAgents). */
  agents: Agent[];
  loading?: boolean;
  /** Message d'erreur API (null = OK) — affiché dans le menu, jamais masqué. */
  error?: string | null;
  /** Agent actif (null = « Sans agent »). État possédé par la page. */
  selectedAgentId: string | null;
  /** Derniers agents utilisés (ids) — section Récents du menu. */
  recentAgentIds?: string[];
  onSelect: (id: string | null) => void;
}

/**
 * Sélecteur d'agent du header chat — symétrique du ModelSelector compact
 * ([Agent ▼] [Model ▼]). Le frontend ne fait que récupérer · afficher ·
 * sélectionner les agents du Core ; « + Nouvel agent » renvoie vers la page
 * /agents existante (aucune création parallèle ici).
 */
export function AgentSelector({
  agents,
  loading,
  error,
  selectedAgentId,
  recentAgentIds = [],
  onSelect,
}: AgentSelectorProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const close = () => {
    setIsOpen(false);
    setSearch("");
  };

  const handleSelect = (id: string | null) => {
    onSelect(id);
    close();
  };

  const q = search.trim().toLowerCase();
  const matches = (a: Agent) =>
    !q ||
    a.name.toLowerCase().includes(q) ||
    (a.description ?? "").toLowerCase().includes(q);

  const recents = recentAgentIds
    .map((id) => agents.find((a) => a.id === id))
    .filter((a): a is Agent => !!a && a.id !== selectedAgentId && matches(a));
  const recentSet = new Set(recents.map((a) => a.id));

  /**
   * Regroupement « General / Spécialisé » conforme au target Open-WebUI,
   * dérivé des VRAIES capabilities déclarées par le Core (core/agents/types.py).
   * - General     : agent sans capability (assistant générique).
   * - Spécialisé  : agent avec ≥ 1 capability (badges visibles dans l'item).
   * Les agents déjà listés dans Récents ne sont pas répétés ici.
   */
  const general = agents.filter(
    (a) =>
      a.id !== selectedAgentId &&
      !recentSet.has(a.id) &&
      matches(a) &&
      !(a.capabilities && a.capabilities.length > 0),
  );
  const specialized = agents.filter(
    (a) =>
      a.id !== selectedAgentId &&
      !recentSet.has(a.id) &&
      matches(a) &&
      !!(a.capabilities && a.capabilities.length > 0),
  );
  const groups = [
    { label: "General", agents: general },
    { label: "Spécialisée", agents: specialized },
  ].filter((g) => g.agents.length > 0);
  const activeAgent = agents.find((a) => a.id === selectedAgentId) ?? null;

  // ── Navigation clavier (pattern Open-WebUI Selector.svelte : flèches + Enter + Escape) ──
  /** Liste aplatie : « Sans agent » (null) puis Récents puis groupes. */
  const flatAgents: (Agent | null)[] = React.useMemo(
    () => [null, ...recents, ...general, ...specialized],
    [recents, general, specialized],
  );
  const [arrowIdx, setArrowIdx] = React.useState(0);
  React.useEffect(() => {
    setArrowIdx(0);
  }, [search]);

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      close();
      return;
    }
    if (flatAgents.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setArrowIdx((i) => Math.min(i + 1, flatAgents.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setArrowIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const target = flatAgents[arrowIdx];
      handleSelect(target ? target.id : null);
      return;
    } else {
      return;
    }
    requestAnimationFrame(() => {
      dropdownRef.current
        ?.querySelector('[data-arrow-selected="true"]')
        ?.scrollIntoView({ block: "center" });
    });
  };

  return (
    <div ref={dropdownRef} className="relative">
      {/* Déclencheur — même gabarit que le trigger compact du ModelSelector */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        title="Changer d'agent"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        className="flex items-center gap-1.5 rounded-md px-1.5 py-1 text-xs text-foreground-tertiary transition-colors hover:bg-bg-3 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-accent/50"
      >
        <Bot className="h-3.5 w-3.5 shrink-0 text-accent/80" />
        <span className="font-medium text-foreground-secondary">
          {loading ? "Agents…" : activeAgent?.name || "Sans agent"}
        </span>
        {activeAgent?.model && (
          <>
            <span>/</span>
            <span className="font-mono">{activeAgent.model}</span>
          </>
        )}
        <ChevronDown
          className={`h-3.5 w-3.5 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {isOpen && (
        <div
          role="listbox"
          aria-label="Sélectionner un agent"
          className="absolute right-0 z-50 mt-1 max-h-96 w-72 overflow-y-auto rounded-lg border border-line-2 bg-bg-2 shadow-lg"
        >
          {/* Recherche */}
          <div className="sticky top-0 border-b border-line-1 bg-bg-2 p-1.5">
            <div className="relative">
              <Search size={13} className="absolute left-2 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                placeholder="Rechercher un agent…"
                autoFocus
                className="h-7 w-full rounded-md border border-line-2 bg-bg-1 pl-7 pr-2 text-xs text-foreground placeholder:text-foreground-tertiary shadow-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
              />
            </div>
          </div>

          {/* Option explicite : mode ETHAN brut */}
          <AgentItem
            name="Sans agent"
            description="ETHAN brut — aucune personnalité"
            isSelected={!selectedAgentId}
            arrowSelected={arrowIdx === 0}
            onSelect={() => handleSelect(null)}
          />

          {recents.length > 0 && <SectionLabel>Récents</SectionLabel>}
          {recents.map((agent) => (
            <AgentItem
              key={agent.id}
              agent={agent}
              isSelected={false}
              arrowSelected={flatAgents[arrowIdx] === agent}
              onSelect={() => handleSelect(agent.id)}
            />
          ))}

          {loading && agents.length === 0 && (
            <p className="px-3 py-4 text-center text-xs text-foreground-tertiary">
              Chargement des agents…
            </p>
          )}

          {!loading && error && agents.length === 0 && (
            <p className="px-3 py-4 text-center text-xs text-red-500">
              Erreur de chargement : {error}
            </p>
          )}

          {!loading && !error && agents.length === 0 && (
            <p className="px-3 py-4 text-center text-xs text-foreground-tertiary">
              Aucun agent créé dans ETHAN.
            </p>
          )}

          {!loading && !error && agents.length > 0 && groups.length === 0 && (
            <p className="px-3 py-4 text-center text-xs text-foreground-tertiary">
              Aucun agent ne correspond à « {search} ».
            </p>
          )}

          {groups.map((group) => (
            <React.Fragment key={group.label}>
              <SectionLabel>{group.label}</SectionLabel>
              {group.agents.map((agent) => (
                <AgentItem
                  key={agent.id}
                  agent={agent}
                  isSelected={false}
                  arrowSelected={flatAgents[arrowIdx] === agent}
                  onSelect={() => handleSelect(agent.id)}
                />
              ))}
            </React.Fragment>
          ))}

          {/* Création : navigation vers l'interface existante — pas de doublon */}
          <button
            type="button"
            onClick={() => {
              close();
              router.push("/agents");
            }}
            className="mt-1 flex w-full items-center gap-2 border-t border-line-1 px-3 py-2 text-sm text-accent hover:bg-bg-3 focus:outline-none focus:ring-2 focus:ring-accent/50"
          >
            <Plus size={14} />
            Nouvel agent…
          </button>
        </div>
      )}
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="px-3 pb-0.5 pt-2 text-[10px] font-semibold uppercase tracking-wider text-foreground-tertiary">
      {children}
    </div>
  );
}

/** Ligne d'agent : nom + modèle par défaut + capacités issues des champs Core. */
function AgentItem({
  agent,
  name,
  description,
  isSelected,
  arrowSelected,
  onSelect,
}: {
  agent?: Agent;
  name?: string;
  description?: string;
  isSelected: boolean;
  /** Item courant de la navigation clavier flèches (pattern Open-WebUI). */
  arrowSelected?: boolean;
  onSelect: () => void;
}) {
  // Compteurs calculés depuis les VRAIS champs Core (aucune invention).
  const skillCount = agent?.skill_ids?.length ?? 0;
  const kbCount = (agent?.metadata?.knowledge_ids as string[] | undefined)?.length ?? 0;
  const toolCount = (agent?.metadata?.tool_ids as string[] | undefined)?.length ?? 0;
  const counts = [
    skillCount > 0 ? `${skillCount} skill${skillCount > 1 ? "s" : ""}` : null,
    kbCount > 0 ? `${kbCount} base${kbCount > 1 ? "s" : ""}` : null,
    toolCount > 0 ? `${toolCount} outil${toolCount > 1 ? "s" : ""}` : null,
  ].filter(Boolean);

  return (
    <div
      role="option"
      aria-selected={isSelected}
      tabIndex={0}
      data-arrow-selected={arrowSelected ? "true" : undefined}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
      onClick={onSelect}
      className={`mx-1 flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 transition-colors ${
        isSelected
          ? "bg-accent/20 text-foreground"
          : "text-foreground-secondary hover:bg-bg-3"
      } ${arrowSelected ? "ring-1 ring-accent/60" : ""}`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">
            {name ?? agent!.name}
          </span>
          {agent?.model && (
            <span className="shrink-0 font-mono text-[10px] text-foreground-tertiary">
              {agent.provider ? `${agent.provider}·` : ""}
              {agent.model}
            </span>
          )}
        </div>
        {(description ?? agent?.description) && (
          <p className="truncate text-xs text-foreground-tertiary">
            {description ?? agent!.description}
          </p>
        )}
        {counts.length > 0 && (
          <p className="truncate text-[10px] text-foreground-tertiary/80">
            {counts.join(" · ")}
          </p>
        )}
      </div>
      {isSelected && (
        <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 shrink-0 text-accent">
          <path
            fillRule="evenodd"
            d="M16.7 5.3a1 1 0 010 1.4l-7.5 7.5a1 1 0 01-1.4 0L3.3 9.7a1 1 0 111.4-1.4l3.8 3.8 6.8-6.8a1 1 0 011.4 0z"
            clipRule="evenodd"
          />
        </svg>
      )}
    </div>
  );
}

