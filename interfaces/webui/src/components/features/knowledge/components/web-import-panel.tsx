"use client";

/**
 * WebImportPanel — import de connaissances depuis une URL (Web Import).
 *
 * Pipeline : URL → Scan (contrôlé, robots.txt) → Preview → Sélection →
 * dossier de destination → configuration RAG → Indexation.
 *
 * Aucune logique métier ici : le scan et l'indexation sont orchestrés par le
 * Core (POST /v1/web-ingest/scan puis /ingest). Cette UI ne fait que
 * configurer, déclencher et refléter la progression retournée.
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Search, Loader2, CheckCircle2, ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useUIStore } from "@/store/ui.store";
import { listFolderTree, type FolderTree } from "@/lib/api/folders";
import { listCollections, type KnowledgeCollection } from "@/lib/api/knowledge";
import { getRagStrategies, type RagStrategyOption } from "@/lib/api/rag";
import {
  scanWebUrl, ingestWebPages, type WebScanPreview, type WebIngestResult,
} from "@/lib/api/web-import";

export function WebImportPanel() {
  const addToast = useUIStore((s) => s.addToast);

  // Scan
  const [url, setUrl] = React.useState("");
  const [maxPages, setMaxPages] = React.useState(10);
  const [maxDepth, setMaxDepth] = React.useState(2);
  const [useSitemap, setUseSitemap] = React.useState(true);
  const [excludePatterns, setExcludePatterns] = React.useState("");
  const [scanning, setScanning] = React.useState(false);
  const [scan, setScan] = React.useState<WebScanPreview | null>(null);
  const [selectedPages, setSelectedPages] = React.useState<Set<string>>(new Set());

  // Destination + configuration
  const [target, setTarget] = React.useState<"collection" | "knowledge">("collection");
  const [folderId, setFolderId] = React.useState("");
  const [newFolderName, setNewFolderName] = React.useState("");
  const [collectionId, setCollectionId] = React.useState("");
  const [newCollectionName, setNewCollectionName] = React.useState("");
  const [strategy, setStrategy] = React.useState("");
  const [embeddingModel, setEmbeddingModel] = React.useState("");
  const [ingesting, setIngesting] = React.useState(false);
  const [result, setResult] = React.useState<WebIngestResult | null>(null);

  // ── ── (FIN SCAN) ── ────────────────────────────────────────────────────
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

  const okPages = scan ? scan.pages.filter((p) => p.status === "ok") : [];

  const runScan = async () => {
    if (!url.trim()) return;
    setScanning(true);
    setScan(null);
    setResult(null);
    setSelectedPages(new Set());
    try {
      const preview = await scanWebUrl({
        url: url.trim(),
        max_pages: Math.max(1, Math.min(50, maxPages)),
        max_depth: Math.max(0, Math.min(5, maxDepth)),
        use_sitemap: useSitemap,
        exclude_patterns: excludePatterns.split(",").map((s) => s.trim()).filter(Boolean),
      });
      setScan(preview);
      // Pré-sélection minimale et explicite : la racine uniquement — jamais tout.
      const root = preview.pages.find((p) => p.status === "ok" && p.depth === 0);
      setSelectedPages(new Set(root ? [root.page_id] : []));
      addToast({ type: "success", message: `${preview.pages.filter((p) => p.status === "ok").length} page(s) récupérable(s) — validez votre sélection` });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Scan échoué" });
    } finally {
      setScanning(false);
    }
  };

  const togglePage = (pageId: string) => {
    const next = new Set(selectedPages);
    if (next.has(pageId)) next.delete(pageId); else next.add(pageId);
    setSelectedPages(next);
  };

  const runIngest = async () => {
    if (!scan || selectedPages.size === 0) return;
    setIngesting(true);
    setResult(null);
    try {
      const res = await ingestWebPages({
        scan_id: scan.scan_id,
        page_ids: Array.from(selectedPages),
        folder_id: folderId || null,
        new_folder_name: newFolderName.trim() || undefined,
        target,
        collection_id: collectionId || null,
        new_collection_name:
          target === "collection" && newCollectionName.trim() ? newCollectionName.trim() : undefined,
        retrieval_strategy: strategy || null,
        embedding_model: embeddingModel.trim() || null,
      });
      setResult(res);
      addToast({ type: "success", message: `${res.indexed_count} page(s) indexée(s)` });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Indexation échouée" });
    } finally {
      setIngesting(false);
    }
  };
  const rerunScan = async () => {
    await runScan();
  };

  return (
    <div className="space-y-4">
      {/* ── Étape 1 : Scan ── */}
      <div className="rounded-lg border border-line-1 bg-bg-1 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-0 flex-1">
            <label className="text-xs font-medium text-foreground-secondary">URL du site ou d'une page</label>
            <Input
              className="mt-1 w-full"
              placeholder="https://docs.example.com/"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runScan()}
            />
          </div>
          <div>
            <label className="text-xs text-foreground-tertiary">Pages max</label>
            <Input type="number" className="mt-1 w-24" min={1} max={50} value={String(maxPages)} onChange={(e) => setMaxPages(Number(e.target.value) || 10)} />
          </div>
          <div>
            <label className="text-xs text-foreground-tertiary">Profondeur</label>
            <Input type="number" className="mt-1 w-20" min={0} max={5} value={String(maxDepth)} onChange={(e) => setMaxDepth(Number(e.target.value) || 0)} />
          </div>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-1.5 text-xs text-foreground-secondary">
            <input type="checkbox" checked={useSitemap} onChange={(e) => setUseSitemap(e.target.checked)} className="accent-accent" />
            Utiliser le sitemap si disponible
          </label>
          <Input
            className="w-64"
            placeholder="Exclure (globs) ex. */api/*, */draft*"
            value={excludePatterns}
            onChange={(e) => setExcludePatterns(e.target.value)}
          />
          <Button variant="primary" onClick={rerunScan} disabled={scanning || !url.trim()}>
            {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            <span className="ml-1">{scanning ? "Scan en cours…" : "Scanner"}</span>
          </Button>
        </div>
        <p className="mt-1 text-[11px] text-foreground-tertiary">
          Scan contrôlé : robots.txt respecté, garde-fous SSRF, bornes strictes. Aucune indexation avant votre validation.
        </p>
      </div>

      {/* ── Étape 2 : Preview + Sélection ── */}
      {scan && (
        <div className="rounded-lg border border-line-1 bg-bg-1 p-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-foreground">
              Preview — {okPages.length} page(s) récupérable(s){scan.sitemap_used ? " · via sitemap" : ""}
            </p>
            <div className="flex gap-1">
              <Button variant="ghost" size="sm" onClick={() => setSelectedPages(new Set(okPages.map((p) => p.page_id)))}>Tout sélectionner</Button>
              <Button variant="ghost" size="sm" onClick={() => setSelectedPages(new Set())}>Aucune</Button>
            </div>
          </div>
          <div className="mt-2 max-h-64 overflow-y-auto rounded-lg border divide-y divide-line-1">
            {scan.pages.map((page) => (
              <label key={page.page_id} className="flex items-start gap-2 px-2 py-1.5 cursor-pointer hover:bg-bg-2">
                <input
                  type="checkbox"
                  disabled={page.status !== "ok"}
                  checked={selectedPages.has(page.page_id)}
                  onChange={() => togglePage(page.page_id)}
                  className="accent-accent mt-0.5"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium text-foreground">{page.title || page.url}</span>
                    {page.duplicate_of && <span className="rounded-full bg-amber-500/15 px-1.5 text-[10px] text-amber-500">doublon</span>}
                  </div>
                  <p className="truncate text-[11px] text-foreground-tertiary">{page.url} · {page.status}{page.depth > 0 ? ` · niv. ${page.depth}` : ""}</p>
                  {page.excerpt && <p className="truncate text-[11px] text-foreground-secondary">{page.excerpt}</p>}
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* ── Étape 3 : Destination + Configuration RAG + Indexation ── */}
      {scan && selectedPages.size > 0 && (
        <div className="rounded-lg border border-line-1 bg-bg-1 p-4">
          <p className="text-xs font-semibold text-foreground-secondary uppercase tracking-wider">Destination &amp; configuration</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <div>
              <label className="text-xs text-foreground-secondary">Cible</label>
              <select className="mt-1 w-full h-9 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm text-foreground" value={target} onChange={(e) => setTarget(e.target.value as "collection" | "knowledge")}>
                <option value="collection">RAG Collection</option>
                <option value="knowledge">Knowledge (nœuds)</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-foreground-secondary">Dossier de destination</label>
              {flatFolders.length > 0 ? (
                <select className="mt-1 w-full h-9 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm text-foreground" value={folderId} onChange={(e) => setFolderId(e.target.value)}>
                  <option value="">— Aucun —</option>
                  {flatFolders.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
                </select>
              ) : (
                <p className="text-[11px] text-foreground-tertiary">Aucun dossier — créez-en un ci-contre.</p>
              )}
            </div>
            <div>
              <label className="text-xs text-foreground-secondary">… ou créer un dossier</label>
              <Input className="mt-1 w-full" placeholder="Nom du nouveau dossier (libre)" value={newFolderName} onChange={(e) => setNewFolderName(e.target.value)} />
            </div>
            {target === "collection" && (
              <>
                <div>
                  <label className="text-xs text-foreground-secondary">RAG Collection</label>
                  {collections.length > 0 ? (
                    <select className="mt-1 w-full h-9 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm text-foreground" value={collectionId} onChange={(e) => setCollectionId(e.target.value)}>
                      <option value="">— Nouvelle collection —</option>
                      {collections.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  ) : (
                    <p className="text-[11px] text-foreground-tertiary">Aucune collection — créez-en une.</p>
                  )}
                </div>
                <div>
                  <label className="text-xs text-foreground-secondary">… ou créer une collection</label>
                  <Input className="mt-1 w-full" placeholder="Nom de la nouvelle collection" value={newCollectionName} onChange={(e) => setNewCollectionName(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-foreground-secondary">Stratégie RAG</label>
                  <select className="mt-1 w-full h-9 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm text-foreground" value={strategy} onChange={(e) => setStrategy(e.target.value)}>
                    <option value="">— Héritée (défaut) —</option>
                    {ragStrategies.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-foreground-secondary">Modèle d&apos;embedding</label>
                  <Input className="mt-1 w-full font-mono text-xs" placeholder="e.g. nomic-embed-text" value={embeddingModel} onChange={(e) => setEmbeddingModel(e.target.value)} />
                </div>
              </>
            )}
          </div>
          <div className="mt-3 flex justify-end gap-2">
            <Button variant="primary" onClick={runIngest} disabled={ingesting}>
              {ingesting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
              <span className="ml-1">Indexer {selectedPages.size} page(s){ingesting ? "…" : ""}</span>
            </Button>
          </div>
        </div>
      )}

      {result && (
        <div className="rounded-lg border border-green-600/30 bg-green-600/10 p-3 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <span className="text-sm text-foreground">
            {result.indexed_count} page(s) indexée(s){result.collection ? ` dans « ${result.collection.name} »` : ""}{result.folder ? ` · dossier « ${result.folder.name} »` : ""}.
          </span>
        </div>
      )}
    </div>
  );
}