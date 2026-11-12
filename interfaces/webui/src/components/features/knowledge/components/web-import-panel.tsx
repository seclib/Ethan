"use client";

/**
 * WebImportPanel — fonctionnalité unique « Web Import » (fusion de
 * l'ancien Web Import URL et de l'ancien Web Inspiration).
 *
 * Deux sources, un seul workflow :
 *   1. Recherche : sujet/requête → collecte multi-moteurs Core
 *      (/v1/web-research/collect, options proxy/VPN via profil réseau) ;
 *   2. URL : scan contrôlé d'un site (/v1/web-ingest/scan, robots.txt).
 *
 * Puis : sélection des pages → destination EXPLICITE (Knowledge global,
 * RAG Collection ou Projet) → import → rapport (pages importées,
 * statut d'indexation, erreurs, doublons ignorés).
 *
 * Aucune logique métier ici : la recherche, le scan et l'indexation sont
 * orchestrés par le Core (web_research_service / web_ingest, pipelines
 * RAG existants). Cette UI ne fait que configurer, déclencher et afficher
 * l'état réel retourné.
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Search, Loader2, CheckCircle2, ArrowRight, Globe, ExternalLink, AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useUIStore } from "@/store/ui.store";
import { listFolderTree, type FolderTree } from "@/lib/api/folders";
import { listCollections, type KnowledgeCollection } from "@/lib/api/knowledge";
import { getRagStrategies, type RagStrategyOption } from "@/lib/api/rag";
import { listProjects, type Project } from "@/lib/api/projects";
import {
  listSearchEngines, listNetworkProfiles,
  type SearchEngine, type NetworkProfileView,
} from "@/lib/api/web-search";
import {
  collectResearch, fetchResearchLimits, importResearchSelection,
  type ImportReport, type ResearchPage,
} from "@/lib/api/web-research";
import {
  scanWebUrl, ingestWebPages, type WebScanPreview, type WebIngestResult,
} from "@/lib/api/web-import";

/** Plafond absolu côté Core (MAX_PAGES_PER_COLLECTION) — repli si /limits indisponible. */
const FALLBACK_MAX_PAGES = 50;
const PAGE_PRESETS = [5, 10, 20, 30, 50];

type SourceMode = "search" | "url";
type Destination = "knowledge" | "collection" | "project";

/** Ligne unifiée (recherche ou scan) affichée dans la liste de sélection. */
interface PageRow {
  /** Identifiant de sélection : url (recherche) ou page_id (scan). */
  id: string;
  url: string;
  title: string;
  detail: string;
}

/** Rapport unifié (recherche web-research ou scan web-ingest). */
interface ImportOutcome {
  destinationLabel: string;
  indexedCount: number;
  importedCount: number;
  failedCount: number;
  skippedDuplicates: number;
  rows: Array<{ title: string; url: string; status: string; error: string | null }>;
}

export function WebImportPanel() {
  const addToast = useUIStore((s) => s.addToast);

  // ── Source ────────────────────────────────────────────────────────────
  const [mode, setMode] = React.useState<SourceMode>("search");

  // Mode Recherche
  const [query, setQuery] = React.useState("");
  const [engines, setEngines] = React.useState<Set<string>>(new Set());
  const [maxResults, setMaxResults] = React.useState(10);
  const [networkProfile, setNetworkProfile] = React.useState("");
  const [collecting, setCollecting] = React.useState(false);
  const [searchPages, setSearchPages] = React.useState<ResearchPage[]>([]);

  // Mode URL
  const [url, setUrl] = React.useState("");
  const [maxPages, setMaxPages] = React.useState(10);
  const [maxDepth, setMaxDepth] = React.useState(2);
  const [useSitemap, setUseSitemap] = React.useState(true);
  const [excludePatterns, setExcludePatterns] = React.useState("");
  const [scanning, setScanning] = React.useState(false);
  const [scan, setScan] = React.useState<WebScanPreview | null>(null);

  // ── Sélection + destination ───────────────────────────────────────────
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set());
  const [destination, setDestination] = React.useState<Destination>("knowledge");
  const [folderId, setFolderId] = React.useState("");
  const [newFolderName, setNewFolderName] = React.useState("");
  const [collectionId, setCollectionId] = React.useState("");
  const [newCollectionName, setNewCollectionName] = React.useState("");
  const [strategy, setStrategy] = React.useState("");
  const [embeddingModel, setEmbeddingModel] = React.useState("");
  const [projectId, setProjectId] = React.useState("");

  const [importing, setImporting] = React.useState(false);
  const [outcome, setOutcome] = React.useState<ImportOutcome | null>(null);

  // ── Référentiels (vues Core, aucune logique) ──────────────────────────
  const { data: engineList = [] } = useQuery<SearchEngine[]>({
    queryKey: ["web-search-engines"],
    queryFn: () => listSearchEngines(),
    staleTime: 300_000,
  });
  const { data: profiles = [] } = useQuery<NetworkProfileView[]>({
    queryKey: ["web-network-profiles"],
    queryFn: () => listNetworkProfiles(),
    staleTime: 300_000,
  });
  const { data: limits } = useQuery<{ max_pages_per_collection: number }>({
    queryKey: ["web-research-limits"],
    queryFn: () => fetchResearchLimits(),
    staleTime: 300_000,
  });
  const maxPagesCap = limits?.max_pages_per_collection ?? FALLBACK_MAX_PAGES;

  const { data: folderTree = [] } = useQuery<FolderTree[]>({
    queryKey: ["folder-tree"],
    queryFn: () => listFolderTree(),
  });
  const flatFolders = React.useMemo(() => {
    const out: FolderTree[] = [];
    const walk = (nodes: FolderTree[]) => {
      for (const n of nodes) { out.push(n); walk(n.children); }
    };
    walk(folderTree);
    return out;
  }, [folderTree]);

  const { data: collections = [] } = useQuery<KnowledgeCollection[]>({
    queryKey: ["knowledgeCollections"],
    queryFn: () => listCollections(),
    staleTime: 10_000,
  });
  const { data: strategiesData } = useQuery({
    queryKey: ["rag-strategies"],
    queryFn: () => getRagStrategies(),
    staleTime: 300_000,
  });
  const ragStrategies: RagStrategyOption[] = strategiesData?.strategies ?? [];

  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: () => listProjects(),
    staleTime: 10_000,
  });
  const selectedProject = projects.find((p) => p.id === projectId) ?? null;
  const selectedCollection = collections.find((c) => c.id === collectionId) ?? null;

  // ── Pages candidates (unifiées) ───────────────────────────────────────
  const pageRows: PageRow[] = React.useMemo(() => {
    if (mode === "search") {
      return searchPages.map((p) => ({
        id: p.url, url: p.url, title: p.title || p.url,
        detail: `${p.source_engine} · ${p.domain}`,
      }));
    }
    return (scan?.pages ?? [])
      .filter((p) => p.status === "ok")
      .map((p) => ({
        id: p.page_id, url: p.url, title: p.title || p.url,
        detail: `${p.text_length.toLocaleString("fr-FR")} caractères`,
      }));
  }, [mode, searchPages, scan]);

  const togglePage = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else if (next.size < maxPagesCap) next.add(id);
      else addToast({ type: "warning", message: `Plafond : ${maxPagesCap} pages maximum.` });
      return next;
    });
  };
  const toggleAll = () => {
    setSelectedIds((prev) =>
      prev.size === pageRows.length ? new Set() : new Set(pageRows.map((p) => p.id)),
    );
  };

  const toggleEngine = (id: string) => {
    setEngines((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // ── Libellé de destination (affiché avant validation) ─────────────────
  const destinationLabel = React.useMemo(() => {
    if (destination === "knowledge") return "Knowledge global (nœuds de connaissance ETHAN)";
    if (destination === "project") {
      return selectedProject
        ? `Projet « ${selectedProject.name} »`
        : "Projet — sélection requise";
    }
    return selectedCollection
      ? `RAG Collection « ${selectedCollection.name} »`
      : newCollectionName.trim()
        ? `Nouvelle RAG Collection « ${newCollectionName.trim()} »`
        : "RAG Collection — nom ou sélection requise";
  }, [destination, selectedProject, selectedCollection, newCollectionName]);

  const destinationValid =
    destination === "knowledge" ||
    (destination === "project" && !!projectId) ||
    (destination === "collection" && (!!collectionId || !!newCollectionName.trim()));

  // ── Actions ───────────────────────────────────────────────────────────
  const resetSelection = () => {
    setSelectedIds(new Set());
    setOutcome(null);
  };

  const runCollect = async () => {
    if (!query.trim()) return;
    setCollecting(true);
    setSearchPages([]);
    setScan(null);
    resetSelection();
    try {
      const res = await collectResearch({
        query: query.trim(),
        engines: engines.size ? [...engines] : undefined,
        max_results_per_engine: maxResults,
        network_profile: networkProfile || undefined,
      });
      setSearchPages(res.research.results);
      const errs = Object.keys(res.research.errors ?? {});
      if (errs.length) {
        addToast({ type: "warning", message: `Moteurs en erreur : ${errs.join(", ")}` });
      }
    } catch (err) {
      addToast({
        type: "error",
        message: `Recherche impossible : ${err instanceof Error ? err.message : "erreur inconnue"}`,
      });
    } finally {
      setCollecting(false);
    }
  };

  const runScan = async () => {
    if (!url.trim()) return;
    setScanning(true);
    setScan(null);
    setSearchPages([]);
    resetSelection();
    try {
      const preview = await scanWebUrl({
        url: url.trim(),
        max_pages: maxPages,
        max_depth: maxDepth,
        use_sitemap: useSitemap,
        exclude_patterns: excludePatterns
          .split(",").map((s) => s.trim()).filter(Boolean),
      });
      setScan(preview);
      if (preview.pages.filter((p) => p.status === "ok").length === 0) {
        addToast({ type: "warning", message: "Aucune page exploitable sur cette URL." });
      }
    } catch (err) {
      addToast({
        type: "error",
        message: `Scan impossible : ${err instanceof Error ? err.message : "erreur inconnue"}`,
      });
    } finally {
      setScanning(false);
    }
  };

  /** Fusionne les deux formats de rapport Core en un rendu unique. */
  const toOutcome = (
    report: ImportReport | WebIngestResult,
    dest: Destination,
  ): ImportOutcome => {
    const rows: ImportOutcome["rows"] = [];
    let indexedCount = 0;
    if ("pages" in report) {
      // ImportReport (web-research)
      for (const p of report.pages) {
        rows.push({ title: p.title, url: p.url, status: p.status, error: p.error });
        indexedCount += p.indexed_count ?? 0;
      }
      return {
        destinationLabel:
          dest === "project"
            ? `Projet ${report.project?.id ? `« ${report.project.id} »` : ""}`
            : dest === "knowledge"
              ? "Knowledge global"
              : report.collection?.name
                ? `RAG Collection « ${report.collection.name} »`
                : "RAG Collection",
        indexedCount,
        importedCount: report.imported_count,
        failedCount: report.failed_count + report.unreachable_count,
        skippedDuplicates: report.skipped_duplicates,
        rows,
      };
    }
    // WebIngestResult (web-ingest)
    for (const p of report.indexed) {
      rows.push({
        title: p.title ?? p.url,
        url: p.url,
        status: "imported",
        error: p.error ?? null,
      });
      indexedCount += 1;
    }
    return {
      destinationLabel:
        dest === "project"
          ? `Projet ${report.project ? `« ${report.project.id} »` : ""}`
          : dest === "knowledge"
            ? "Knowledge global"
            : report.collection?.name
              ? `RAG Collection « ${report.collection.name} »`
              : "RAG Collection",
      indexedCount,
      importedCount: report.indexed_count,
      failedCount: 0,
      skippedDuplicates: report.skipped_duplicates.length,
      rows,
    };
  };

  const runImport = async () => {
    if (!destinationValid || selectedIds.size === 0) return;
    setImporting(true);
    setOutcome(null);
    try {
      let report: ImportReport | WebIngestResult;
      if (mode === "search") {
        report = await importResearchSelection({
          urls: pageRows.filter((p) => selectedIds.has(p.id)).map((p) => p.url),
          target: destination,
          collection_id: destination === "collection" ? collectionId || undefined : undefined,
          collection_name:
            destination === "collection" && !collectionId
              ? newCollectionName.trim()
              : undefined,
          project_id: destination === "project" ? projectId : undefined,
        });
      } else {
        report = await ingestWebPages({
          scan_id: scan!.scan_id,
          page_ids: [...selectedIds],
          target: destination,
          folder_id: folderId || undefined,
          new_folder_name: !folderId && newFolderName.trim() ? newFolderName.trim() : undefined,
          collection_id: destination === "collection" ? collectionId || undefined : undefined,
          new_collection_name:
            destination === "collection" && !collectionId
              ? newCollectionName.trim()
              : undefined,
          retrieval_strategy: destination === "collection" ? strategy || undefined : undefined,
          embedding_model:
            destination === "collection" ? embeddingModel.trim() || undefined : undefined,
          project_id: destination === "project" ? projectId : undefined,
        });
      }
      const out = toOutcome(report, destination);
      setOutcome(out);
      addToast({
        type: out.failedCount > 0 ? "warning" : "success",
        message: `${out.indexedCount} page(s) indexée(s) → ${out.destinationLabel}`,
      });
    } catch (err) {
      addToast({
        type: "error",
        message: `Import échoué : ${err instanceof Error ? err.message : "erreur inconnue"}`,
      });
    } finally {
      setImporting(false);
    }
  };

  const switchMode = (m: SourceMode) => {
    setMode(m);
    setScan(null);
    setSearchPages([]);
    resetSelection();
  };

  // ── Rendu ─────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col gap-4 pb-6">
      {/* ── Source : Recherche | URL ─────────────────────────────────── */}
      <div className="flex items-center gap-2">
        {(["search", "url"] as SourceMode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => switchMode(m)}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors ${
              mode === m
                ? "bg-primary/10 text-primary font-medium"
                : "text-foreground-secondary hover:bg-muted"
            }`}
          >
            {m === "search" ? <Search size={14} /> : <Globe size={14} />}
            {m === "search" ? "Recherche par sujet" : "URL directe"}
          </button>
        ))}
      </div>

      {mode === "search" ? (
        <div className="rounded-lg border border-line-1 bg-bg-1 p-3">
          <div className="grid gap-2">
            <label className="text-xs text-foreground-secondary">Sujet ou requête</label>
            <Input
              placeholder="ex. : retrieval augmented generation — bonnes pratiques"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runCollect()}
            />
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <span className="text-xs text-foreground-secondary">Moteurs :</span>
              {engineList.map((e) => (
                <label key={e.id} className="flex items-center gap-1 text-xs text-foreground">
                  <input
                    type="checkbox"
                    checked={engines.has(e.id)}
                    onChange={() => toggleEngine(e.id)}
                  />
                  {e.label}
                </label>
              ))}
              {engineList.length === 0 && (
                <span className="text-[11px] text-foreground-tertiary">
                  Aucun moteur configuré côté Core.
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <span className="text-xs text-foreground-secondary">Résultats / moteur :</span>
              {PAGE_PRESETS.filter((n) => n <= maxPagesCap).map((n) => (
                <label key={n} className="flex items-center gap-1 text-xs text-foreground">
                  <input
                    type="radio"
                    name="max-results"
                    checked={maxResults === n}
                    onChange={() => setMaxResults(n)}
                  />
                  {n}
                </label>
              ))}
            </div>
            {profiles.length > 0 && (
              <div className="pt-1">
                <label className="text-xs text-foreground-secondary">
                  Profil réseau (proxy/VPN — credentials Core uniquement)
                </label>
                <select
                  className="mt-1 w-full h-9 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm text-foreground"
                  value={networkProfile}
                  onChange={(e) => setNetworkProfile(e.target.value)}
                >
                  <option value="">— Direct (aucun proxy) —</option>
                  {profiles
                    .filter((p) => p.enabled)
                    .map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.id} ({p.type}
                        {p.host ? ` · ${p.host}` : ""})
                      </option>
                    ))}
                </select>
              </div>
            )}
          </div>
          <div className="mt-3 flex justify-end">
            <Button variant="secondary" onClick={runCollect} disabled={collecting || !query.trim()}>
              {collecting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              <span className="ml-1">Rechercher</span>
            </Button>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-line-1 bg-bg-1 p-3">
          <div className="grid gap-2">
            <label className="text-xs text-foreground-secondary">URL du site</label>
            <Input
              placeholder="https://exemple.com/docs"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runScan()}
            />
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <span className="text-xs text-foreground-secondary">Pages max :</span>
              {PAGE_PRESETS.filter((n) => n <= maxPagesCap).map((n) => (
                <label key={n} className="flex items-center gap-1 text-xs text-foreground">
                  <input
                    type="radio"
                    name="scan-max-pages"
                    checked={maxPages === n}
                    onChange={() => setMaxPages(n)}
                  />
                  {n}
                </label>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex items-center gap-1 text-xs text-foreground">
                <input
                  type="checkbox"
                  checked={useSitemap}
                  onChange={(e) => setUseSitemap(e.target.checked)}
                />
                Utiliser le sitemap
              </label>
              <span className="text-xs text-foreground-secondary">Profondeur :</span>
              {[1, 2, 3].map((d) => (
                <label key={d} className="flex items-center gap-1 text-xs text-foreground">
                  <input
                    type="radio"
                    name="scan-depth"
                    checked={maxDepth === d}
                    onChange={() => setMaxDepth(d)}
                  />
                  {d}
                </label>
              ))}
            </div>
            <div className="pt-1">
              <label className="text-xs text-foreground-secondary">
                Exclusions (motifs séparés par des virgules)
              </label>
              <Input
                className="mt-1 w-full"
                placeholder="ex. : /blog/, */archive/*"
                value={excludePatterns}
                onChange={(e) => setExcludePatterns(e.target.value)}
              />
            </div>
          </div>
          <div className="mt-3 flex justify-end">
            <Button variant="secondary" onClick={runScan} disabled={scanning || !url.trim()}>
              {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Globe className="h-4 w-4" />}
              <span className="ml-1">Scanner (aperçu — aucune indexation)</span>
            </Button>
          </div>
        </div>
      )}

      {/* ── Pages candidates ─────────────────────────────────────────── */}
      {pageRows.length > 0 && (
        <div className="rounded-lg border border-line-1 bg-bg-1 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs font-medium text-foreground-secondary">
              Pages candidates ({pageRows.length}) — sélection : {selectedIds.size}/{maxPagesCap}
            </p>
            <Button variant="ghost" size="sm" onClick={toggleAll}>
              {selectedIds.size === pageRows.length ? "Tout désélectionner" : "Tout sélectionner"}
            </Button>
          </div>
          <div className="max-h-72 space-y-1 overflow-y-auto">
            {pageRows.map((p) => (
              <label
                key={p.id}
                className="flex cursor-pointer items-start gap-2 rounded-lg p-1.5 hover:bg-bg-2"
              >
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={selectedIds.has(p.id)}
                  onChange={() => togglePage(p.id)}
                />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm text-foreground">{p.title}</span>
                  <span className="flex items-center gap-1 text-[11px] text-foreground-tertiary">
                    <ExternalLink size={10} />
                    <span className="truncate">{p.url}</span>
                    <span>· {p.detail}</span>
                  </span>
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* ── Destination explicite ────────────────────────────────────── */}
      {pageRows.length > 0 && (
        <div className="rounded-lg border border-line-1 bg-bg-1 p-3">
          <p className="mb-2 text-xs font-medium text-foreground-secondary">
            Destination — où le Knowledge sera créé
          </p>
          <div className="grid gap-2">
            {(
              [
                ["knowledge", "Knowledge global"],
                ["collection", "RAG Collection (existante ou nouvelle)"],
                ["project", "Projet existant"],
              ] as Array<[Destination, string]>
            ).map(([value, label]) => (
              <label key={value} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="radio"
                  name="destination"
                  checked={destination === value}
                  onChange={() => setDestination(value)}
                />
                {label}
              </label>
            ))}
          </div>

          {destination === "project" && (
            <div className="mt-2">
              <label className="text-xs text-foreground-secondary">Projet cible</label>
              {projects.length > 0 ? (
                <select
                  className="mt-1 w-full h-9 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm text-foreground"
                  value={projectId}
                  onChange={(e) => setProjectId(e.target.value)}
                >
                  <option value="">— Sélectionner un projet —</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              ) : (
                <p className="mt-1 text-[11px] text-foreground-tertiary">
                  Aucun projet accessible — créez-en un dans l&apos;espace Projets.
                </p>
              )}
            </div>
          )}

          {destination === "collection" && (
            <>
              <div className="mt-2">
                <label className="text-xs text-foreground-secondary">RAG Collection existante</label>
                {collections.length > 0 ? (
                  <select
                    className="mt-1 w-full h-9 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm text-foreground"
                    value={collectionId}
                    onChange={(e) => setCollectionId(e.target.value)}
                  >
                    <option value="">— Nouvelle collection —</option>
                    {collections.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                ) : (
                  <p className="mt-1 text-[11px] text-foreground-tertiary">
                    Aucune collection — un nom ci-dessous en créera une.
                  </p>
                )}
              </div>
              <div className="mt-2">
                <label className="text-xs text-foreground-secondary">… ou créer une collection</label>
                <Input
                  className="mt-1 w-full"
                  placeholder="Nom de la nouvelle collection"
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                />
              </div>
              {mode === "url" && (
                <>
                  <div className="mt-2">
                    <label className="text-xs text-foreground-secondary">Stratégie RAG</label>
                    <select
                      className="mt-1 w-full h-9 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm text-foreground"
                      value={strategy}
                      onChange={(e) => setStrategy(e.target.value)}
                    >
                      <option value="">— Héritée (défaut) —</option>
                      {ragStrategies.map((s) => (
                        <option key={s.id} value={s.id}>{s.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="mt-2">
                    <label className="text-xs text-foreground-secondary">
                      Modèle d&apos;embedding
                    </label>
                    <Input
                      className="mt-1 w-full font-mono text-xs"
                      placeholder="e.g. nomic-embed-text"
                      value={embeddingModel}
                      onChange={(e) => setEmbeddingModel(e.target.value)}
                    />
                  </div>
                </>
              )}
            </>
          )}

          {/* Dossier : organisation optionnelle (mode URL uniquement) */}
          {mode === "url" && (
            <div className="mt-2 grid gap-2">
              <div>
                <label className="text-xs text-foreground-secondary">
                  Dossier (organisation optionnelle)
                </label>
                {flatFolders.length > 0 ? (
                  <select
                    className="mt-1 w-full h-9 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm text-foreground"
                    value={folderId}
                    onChange={(e) => setFolderId(e.target.value)}
                  >
                    <option value="">— Aucun —</option>
                    {flatFolders.map((f) => (
                      <option key={f.id} value={f.id}>{f.name}</option>
                    ))}
                  </select>
                ) : (
                  <p className="mt-1 text-[11px] text-foreground-tertiary">
                    Aucun dossier — créez-en un ci-contre.
                  </p>
                )}
              </div>
              <div>
                <label className="text-xs text-foreground-secondary">
                  … ou créer un dossier
                </label>
                <Input
                  className="mt-1 w-full"
                  placeholder="Nom du nouveau dossier (libre)"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                />
              </div>
            </div>
          )}

          {/* Confirmation de destination AVANT validation */}
          <p className="mt-3 rounded-lg border border-line-1 bg-bg-2 px-2 py-1.5 text-xs text-foreground-secondary">
            Destination : <span className="font-medium text-foreground">{destinationLabel}</span>
            {" · "}
            {selectedIds.size} page(s) sélectionnée(s)
          </p>
          <div className="mt-3 flex justify-end">
            <Button
              variant="primary"
              onClick={runImport}
              disabled={importing || !destinationValid || selectedIds.size === 0}
            >
              {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
              <span className="ml-1">
                Importer {selectedIds.size} page(s) vers {destinationLabel}
              </span>
            </Button>
          </div>
        </div>
      )}

      {/* ── Rapport d'import ─────────────────────────────────────────── */}
      {outcome && (
        <div className="rounded-lg border border-line-1 bg-bg-1 p-3">
          <div className="mb-2 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <span className="text-sm text-foreground">
              {outcome.indexedCount} page(s) indexée(s) → {outcome.destinationLabel}
            </span>
          </div>
          <div className="mb-2 flex flex-wrap gap-3 text-[11px] text-foreground-tertiary">
            <span>Importées : {outcome.importedCount}</span>
            {outcome.failedCount > 0 && (
              <span className="text-amber-500">Échecs/injoignables : {outcome.failedCount}</span>
            )}
            {outcome.skippedDuplicates > 0 && (
              <span>Doublons ignorés : {outcome.skippedDuplicates}</span>
            )}
          </div>
          <div className="max-h-48 space-y-1 overflow-y-auto">
            {outcome.rows.map((r) => (
              <div key={r.url} className="flex items-start gap-2 text-xs">
                {r.status === "imported" ? (
                  <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-green-600" />
                ) : (
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-amber-500" />
                )}
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-foreground">{r.title}</span>
                  {r.error && (
                    <span className="block truncate text-[11px] text-amber-500">{r.error}</span>
                  )}
                </span>
                <span className="shrink-0 text-[10px] uppercase text-foreground-tertiary">
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
