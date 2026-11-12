"use client";

/**
 * ETHAN WebUI — PluginPicker : sélection compacte des plugins pour la
 * conversation (accès depuis le composer, bouton Plugins).
 *
 * Source de vérité : PluginRegistry Core (GET /v1/plugins). Le picker liste
 * les plugins installés/actifs (Suggested = featured du catalogue) ; la
 * sélection est renvoyée à la page propriétaire qui l'envoie au backend
 * (plugin_ids → les tools référencés sont injectés dans le mécanisme
 * EXISTANT tool_ids par le Core — pas de décision d'outil côté WebUI).
 *
 * Lisibilité : popover opaque (aucun backdrop-blur, aucune transparence).
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { listPlugins, type PluginInfo } from "@/lib/api/plugins";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Check, Puzzle, Search } from "lucide-react";

export interface PluginPickerProps {
  /** Plugins sélectionnés pour la conversation (ids). */
  selectedIds: string[];
  onToggle: (pluginId: string) => void;
  /** Navigation vers la page Plugins (gestion/installation). */
  onManage?: () => void;
}

export function PluginPicker({ selectedIds, onToggle, onManage }: PluginPickerProps) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");

  const { data: plugins = [], isLoading } = useQuery({
    queryKey: ["plugins"],
    queryFn: listPlugins,
    retry: false,
  });

  // Sélectionnables : installés et actifs (arbitrage Core). Les plugins
  // disponibles non installés ne peuvent pas être activés ici — lien vers
  // la page Plugins pour la gestion.
  const usable = plugins.filter((p) => p.installed && p.status === "active");
  const q = search.trim().toLowerCase();
  const filtered = q
    ? usable.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q),
      )
    : usable;
  const suggested = filtered.filter((p) => p.featured && !selectedIds.includes(p.id));
  const selected = filtered.filter((p) => selectedIds.includes(p.id));
  const other = filtered.filter((p) => !p.featured && !selectedIds.includes(p.id));

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 rounded-full text-foreground-secondary hover:bg-accent/10 hover:text-accent"
          title="Plugins"
          aria-label="Plugins de la conversation"
          aria-expanded={open}
        >
          <Puzzle size={14} />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-72 p-0">
        <div className="flex items-center gap-2 border-b border-line-1 px-3 py-2">
          <Search size={13} className="shrink-0 text-foreground-tertiary" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search plugins..."
            className="h-7 border-0 bg-transparent px-0 text-xs focus-visible:ring-0"
            aria-label="Rechercher un plugin"
          />
        </div>

        <div className="max-h-64 overflow-y-auto p-1.5">
          {isLoading ? (
            <div className="flex justify-center py-4"><Spinner /></div>
          ) : usable.length === 0 ? (
            <div className="px-2 py-4 text-center">
              <p className="text-xs text-foreground-secondary">Aucun plugin actif</p>
              <button
                className="mt-1 text-[11px] text-accent hover:underline"
                onClick={() => { setOpen(false); onManage?.(); }}
              >
                Gérer les plugins
              </button>
            </div>
          ) : (
            <>
              {selected.length > 0 && (
                <PickerSection title="Activés">
                  {selected.map((p) => (
                    <PickerRow key={p.id} plugin={p} checked onToggle={onToggle} />
                  ))}
                </PickerSection>
              )}
              {suggested.length > 0 && (
                <PickerSection title="Suggested">
                  {suggested.map((p) => (
                    <PickerRow key={p.id} plugin={p} checked={false} onToggle={onToggle} />
                  ))}
                </PickerSection>
              )}
              {other.length > 0 && (
                <PickerSection title="Installed">
                  {other.map((p) => (
                    <PickerRow key={p.id} plugin={p} checked={false} onToggle={onToggle} />
                  ))}
                </PickerSection>
              )}
            </>
          )}
        </div>

        <div className="border-t border-line-1 px-3 py-1.5">
          <button
            className="text-[11px] text-accent hover:underline"
            onClick={() => { setOpen(false); onManage?.(); }}
          >
            Discover plugins…
          </button>
        </div>
      </PopoverContent>
    </Popover>
  );
}

function PickerSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-1">
      <p className="px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-foreground-tertiary">
        {title}
      </p>
      {children}
    </div>
  );
}

function PickerRow({
  plugin, checked, onToggle,
}: {
  plugin: PluginInfo;
  checked: boolean;
  onToggle: (id: string) => void;
}) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      onClick={() => onToggle(plugin.id)}
      className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs text-foreground transition-colors hover:bg-elevated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-accent/10 text-accent text-[10px] font-semibold">
        {plugin.name.slice(0, 1).toUpperCase()}
      </span>
      <span className="min-w-0 flex-1 truncate">{plugin.name}</span>
      {checked && <Check size={12} className="shrink-0 text-green-500" />}
    </button>
  );
}

