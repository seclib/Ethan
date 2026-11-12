"use client";

/**
 * KnowledgeHub — cockpit unifié d'organisation des connaissances ETHAN.
 *
 * Onglets : Tous les dossiers · Toutes les Knowledge · RAG Collections ·
 * Web Import (fonctionnalité unique : recherche multi-moteurs ou
 * URL → sélection → destination explicite → indexation).  Chaque panneau
 * réutilise le workspace Core existant (FoldersWorkspace, KnowledgeWorkspace)
 * ou une vue dédiée (RagCollectionsView, WebImportPanel).  Aucune logique
 * métier ici : chaque vue transmet des intentions au Core et affiche l'état
 * retourné.
 *
 * NOTE (10/11/2026) — l'onglet « Toutes les Skills » a été supprimé de ce
 * hub : la fonctionnalité Skills est accessible depuis Workspaces → Skills
 * (sidebar, route /skills) — doublon supprimé conformément à la règle
 * anti-doublon.
 *
 * NOTE (11/11/2026) — l'onglet « Library » a été supprimé à son tour : la
 * Library est une capacité de premier niveau servie par la route dédiée
 * `/library` (sidebar Workspaces). Ce hub ne doit plus interpréter
 * `?view=library` ni `#library` : une capacité, une destination.
 */

import * as React from "react";
import {
  FolderTree, Database, Layers, Shapes, Network, Search,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { FoldersWorkspace } from "@/components/features/folders/components/folders-workspace";
import { KnowledgeBrowser } from "@/components/features/knowledge/components/knowledge-browser";
import { KnowledgeWorkspace } from "@/components/features/knowledge/components/knowledge-workspace";
import { RagCollectionsView } from "@/components/features/knowledge/components/rag-collections-view";
import { WebImportPanel } from "@/components/features/knowledge/components/web-import-panel";
import { WebSearchPanel } from "@/components/features/knowledge/components/web-search-panel";
import { DomainsWorkspace } from "@/components/features/domains/components/domains-workspace";

type HubTab = "browser" | "domains" | "folders" | "knowledge" | "rag" | "web" | "web-search";

const TABS: Array<{ id: HubTab; label: string; icon: React.ComponentType<{ size?: number | string; className?: string }> }> = [
  { id: "browser", label: "Navigateur", icon: FolderTree },
  { id: "web-search", label: "Recherche Web", icon: Search },
  { id: "domains", label: "Domains", icon: Shapes },
  { id: "folders", label: "Tous les dossiers", icon: FolderTree },
  { id: "knowledge", label: "Toutes les Knowledge", icon: Database },
  { id: "rag", label: "RAG Collections", icon: Layers },
  { id: "web", label: "Web Import", icon: Network },
];

/** `?view=` : lien profond vers un onglet précis (anciennes routes). */
function isHubTab(value: string | null): value is HubTab {
  return value !== null && TABS.some((t) => t.id === value);
}

export function KnowledgeHub() {
  const [tab, setTab] = React.useState<HubTab>("domains");
  const [search, setSearch] = React.useState("");

  // Lien profond : on lit l'URL après montage (évite `useSearchParams`, qui
  // imposerait un Suspense boundary pour une page entièrement cliente).
  React.useEffect(() => {
    const view = new URLSearchParams(window.location.search).get("view");
    if (isHubTab(view)) setTab(view);
  }, []);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="mb-2 flex items-center justify-between gap-3 border-b border-line-1 pb-2">
        <div className="flex flex-wrap items-center gap-1">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              aria-current={tab === id ? "page" : undefined}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors ${
                tab === id
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-foreground-secondary hover:bg-muted"
              }`}
              onClick={() => setTab(id)}
            >
              <Icon size={14} className={tab === id ? "text-primary" : "text-muted-foreground"} />
              {label}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="w-56 pl-7"
            placeholder="Rechercher (tout le workspace)…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

                                                <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === "browser" && <KnowledgeBrowser />}
        {tab === "domains" && <DomainsWorkspace />}
        {tab === "folders" && <FoldersWorkspace />}
        {tab === "knowledge" && <KnowledgeWorkspace />}
        {tab === "rag" && <RagCollectionsView />}
        {tab === "web-search" && <WebSearchPanel />}
        {tab === "web" && <WebImportPanel />}
      </div>
      <p className="mt-1 text-[11px] text-foreground-tertiary">
        Noms et catégories libres — ETHAN n’impose ni dossier ni classification.
        Aucune ressource globale n’est automatiquement injectée. Opérations longues exécutées par le Runtime (progression réelle).
      </p>
    </div>
  );
}