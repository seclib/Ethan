"use client";

/**
 * KnowledgeHub — cockpit unifié d'organisation des connaissances ETHAN.
 *
 * Onglets : Tous les dossiers · Toutes les Knowledge · RAG Collections ·
 * Skills · Library · Web Import (fonctionnalité unique : recherche multi-moteurs ou
 * URL → sélection → destination explicite → indexation).  Chaque panneau
 * réutilise le workspace Core existant (FoldersWorkspace, KnowledgeWorkspace,
 * LibraryWorkspace, SkillsWorkspace) ou une vue dédiée (RagCollectionsView,
 * WebImportPanel).  Aucune logique métier ici : chaque vue transmet des
 * intentions au Core et affiche l'état retourné.
 *
 * CONSOLIDATION (30/09/2026) — la Library est un onglet, plus une page
 * séparée : `LibraryWorkspace` et `KnowledgeHub` interrogeaient les MÊMES
 * endpoints Core (/v1/knowledge, /v1/knowledge/collections, /v1/rag/documents,
 * /v1/projects/{id}/documents, /files — cf. docs/design/2026-10-01-cartographie-webui-ux.md
 * §5.1). Deux surfaces pour un seul jeu de données. La route /library reste
 * valide en lien profond : elle redirige ici avec ?view=library.
 */

import * as React from "react";
import {
  FolderTree, Database, Layers, Shapes, Sparkles, Network, Search, Library,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { FoldersWorkspace } from "@/components/features/folders/components/folders-workspace";
import { KnowledgeBrowser } from "@/components/features/knowledge/components/knowledge-browser";
import { KnowledgeWorkspace } from "@/components/features/knowledge/components/knowledge-workspace";
import { RagCollectionsView } from "@/components/features/knowledge/components/rag-collections-view";
import { WebImportPanel } from "@/components/features/knowledge/components/web-import-panel";
import { WebSearchPanel } from "@/components/features/knowledge/components/web-search-panel";
import { SkillsWorkspace } from "@/components/features/skills/components/skills-workspace";
import { DomainsWorkspace } from "@/components/features/domains/components/domains-workspace";
import { LibraryWorkspace } from "@/components/features/library/library-workspace";

type HubTab = "browser" | "domains" | "folders" | "knowledge" | "library" | "rag" | "skills" | "web" | "web-search";

const TABS: Array<{ id: HubTab; label: string; icon: React.ComponentType<{ size?: number | string; className?: string }> }> = [
  { id: "browser", label: "Navigateur", icon: FolderTree },
  { id: "web-search", label: "Recherche Web", icon: Search },
  { id: "domains", label: "Domains", icon: Shapes },
  { id: "folders", label: "Tous les dossiers", icon: FolderTree },
  { id: "knowledge", label: "Toutes les Knowledge", icon: Database },
  { id: "library", label: "Library", icon: Library },
  { id: "rag", label: "RAG Collections", icon: Layers },
  { id: "skills", label: "Toutes les Skills", icon: Sparkles },
  { id: "web", label: "Web Import", icon: Network },
];

/** `?view=library` : lien profond vers un onglet précis (anciennes routes). */
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
    else if (window.location.hash === "#library") setTab("library");
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
        {tab === "library" && <LibraryWorkspace />}
        {tab === "rag" && <RagCollectionsView />}
        {tab === "web-search" && <WebSearchPanel />}
        {tab === "skills" && <SkillsWorkspace />}
        {tab === "web" && <WebImportPanel />}
      </div>
      <p className="mt-1 text-[11px] text-foreground-tertiary">
        Noms et catégories libres — ETHAN n’impose ni dossier ni classification.
        Aucune ressource globale n’est automatiquement injectée. Opérations longues exécutées par le Runtime (progression réelle).
      </p>
    </div>
  );
}