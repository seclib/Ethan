"use client";

/**
 * KnowledgeBrowser — navigation local-first Collections ⇄ Dossiers ⇄ Ressources.
 *
 * Client passif du Core : la sidebar liste les collections (/v1/knowledge/
 * collections), l'arbre filtre les dossiers par collection (/v1/folders/tree?
 * collection_id=), le listing résout les ressources classées (/v1/folders/{id}/
 * resources) ou les documents RAG à la racine (/v1/knowledge/collections/{id}/
 * documents).  Aucune logique métier : chaque action transmet une intention
 * (create/rename/delete) au Core et affiche l'état retourné.
 */

import * as React from "react";
import {
  ChevronRight, Folder as FolderIcon, FolderPlus, Library, Pencil,
  Plus, Trash2, FileText, Image as ImageIcon, Loader2, AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useUIStore } from "@/store/ui.store";
import {
  createCollection, deleteCollection, getCollection, listCollectionDocuments,
  listCollections, updateCollection,
  type KnowledgeCollection, type RagDocument,
} from "@/lib/api/knowledge";
import {
  createFolder, deleteFolder, listFolderResources, listFolderTree,
  updateFolder, type FolderResource, type FolderTree,
} from "@/lib/api/folders";

interface CollectionMeta {
  collection: KnowledgeCollection | null;
  loading: boolean;
}

/** Fil d'Ariane : chaîne de parents du dossier sélectionné (root → cible). */
function breadcrumbTrail(
  tree: FolderTree[],
  folderId: string | null,
): FolderTree[] {
  if (!folderId) return [];
  const byId = new Map<string, FolderTree>();
  const walk = (nodes: FolderTree[]) => {
    for (const n of nodes) {
      byId.set(n.id, n);
      walk(n.children);
    }
  };
  walk(tree);
  const trail: FolderTree[] = [];
  let cur = byId.get(folderId);
  while (cur) {
    trail.unshift(cur);
    cur = cur.parent_id ? byId.get(cur.parent_id) : undefined;
  }
  return trail;
}

/** Nœud d'arbre récursif (sélection + chevron d'ouverture). */
function FolderNode({
  node, depth, selectedId, onSelect,
}: {
  node: FolderTree;
  depth: number;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [open, setOpen] = React.useState(depth < 1);
  const hasChildren = node.children.length > 0;
  return (
    <div>
      <button
        type="button"
        onClick={() => onSelect(node.id)}
        className={cn(
          "flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-left text-sm transition-colors",
          selectedId === node.id
            ? "bg-accent/15 text-accent"
            : "text-foreground-secondary hover:bg-bg-3",
        )}
        style={{ paddingLeft: `${8 + depth * 14}px` }}
      >
        <button
          type="button"
          aria-label={open ? "Replier" : "Déplier"}
          onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}
          className={cn(
            "flex h-4 w-4 shrink-0 items-center justify-center rounded transition-transform",
            !hasChildren && "invisible",
            open && "rotate-90",
          )}
        >
          <ChevronRight size={12} />
        </button>
        <FolderIcon size={14} className="shrink-0" />
        <span className="truncate">{node.name}</span>
        {node.resource_count > 0 && (
          <span className="ml-auto text-xs text-muted-foreground">
            {node.resource_count}
          </span>
        )}
      </button>
      {open &&
        node.children.map((child) => (
          <FolderNode
            key={child.id}
            node={child}
            depth={depth + 1}
            selectedId={selectedId}
            onSelect={onSelect}
          />
        ))}
    </div>
  );
}

export function KnowledgeBrowser() {
  const addToast = useUIStore((s) => s.addToast);

  // ── Collections (sidebar) ────────────────────────────────────────────
  const [collections, setCollections] = React.useState<KnowledgeCollection[]>([]);
  const [collectionsLoading, setCollectionsLoading] = React.useState(true);
  const [collectionsError, setCollectionsError] = React.useState<string | null>(null);
  const [selectedCollectionId, setSelectedCollectionId] = React.useState<string | null>(null);
  const [collectionMeta, setCollectionMeta] = React.useState<CollectionMeta>({ collection: null, loading: false });

  // ── Dossiers (arbre filtré par collection) ───────────────────────────
  const [tree, setTree] = React.useState<FolderTree[]>([]);
  const [treeLoading, setTreeLoading] = React.useState(false);
  const [selectedFolderId, setSelectedFolderId] = React.useState<string | null>(null);

  // ── Ressources ───────────────────────────────────────────────────────
  const [resources, setResources] = React.useState<FolderResource[]>([]);
  const [docs, setDocs] = React.useState<RagDocument[] | null>(null);
  const [resourcesLoading, setResourcesLoading] = React.useState(false);

  const reloadCollections = React.useCallback(async () => {
    setCollectionsLoading(true);
    setCollectionsError(null);
    try {
      setCollections(await listCollections());
    } catch (err) {
      setCollectionsError(err instanceof Error ? err.message : "Erreur de chargement");
    } finally {
      setCollectionsLoading(false);
    }
  }, []);

  React.useEffect(() => { void reloadCollections(); }, [reloadCollections]);

  // Métadonnées de la collection sélectionnée
  React.useEffect(() => {
    if (!selectedCollectionId) { setCollectionMeta({ collection: null, loading: false }); return; }
    setCollectionMeta((m) => ({ ...m, loading: true }));
    getCollection(selectedCollectionId)
      .then((c) => setCollectionMeta({ collection: c, loading: false }))
      .catch(() => setCollectionMeta({ collection: null, loading: false }));
  }, [selectedCollectionId]);

  // Arbre des dossiers (filtré par collection côté Core)
  React.useEffect(() => {
    if (!selectedCollectionId) { setTree([]); return; }
    let cancelled = false;
    setTreeLoading(true);
    listFolderTree(undefined, selectedCollectionId)
      .then((t) => { if (!cancelled) setTree(t); })
      .catch(() => { if (!cancelled) setTree([]); })
      .finally(() => { if (!cancelled) setTreeLoading(false); });
    return () => { cancelled = true; };
  }, [selectedCollectionId]);

  // Ressources : dossier sélectionné → classées ; sinon → documents RAG racine
  React.useEffect(() => {
    let cancelled = false;
    setResourcesLoading(true);
    setResources([]); setDocs(null);
    (async () => {
      try {
        if (selectedFolderId) {
          const res = await listFolderResources(selectedFolderId);
          if (!cancelled) setResources(res);
        } else if (selectedCollectionId) {
          const d = await listCollectionDocuments(selectedCollectionId);
          if (!cancelled) setDocs(d);
        }
      } catch { /* état vide géré par le rendu */ }
      finally { if (!cancelled) setResourcesLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [selectedFolderId, selectedCollectionId]);

  // ── Actions (intentions → Core) ──────────────────────────────────────
  const [createCollectionOpen, setCreateCollectionOpen] = React.useState(false);
  const [newCollectionName, setNewCollectionName] = React.useState("");
  const [newCollectionDesc, setNewCollectionDesc] = React.useState("");

  const [createFolderOpen, setCreateFolderOpen] = React.useState(false);
  const [newFolderName, setNewFolderName] = React.useState("");
  const [newFolderParentId, setNewFolderParentId] = React.useState<string | null>(null);

  const [renameTarget, setRenameTarget] = React.useState<
    { kind: "collection" | "folder"; id: string; name: string } | null
  >(null);
  const [renameValue, setRenameValue] = React.useState("");
  const [deleteTarget, setDeleteTarget] = React.useState<
    { kind: "collection" | "folder"; id: string; name: string } | null
  >(null);

  const selectedFolder = React.useMemo(() => {
    const walk = (nodes: FolderTree[]): FolderTree | null => {
      for (const n of nodes) {
        if (n.id === selectedFolderId) return n;
        const hit = walk(n.children);
        if (hit) return hit;
      }
      return null;
    };
    return walk(tree);
  }, [tree, selectedFolderId]);

  const trail = React.useMemo(
    () => breadcrumbTrail(tree, selectedFolderId),
    [tree, selectedFolderId],
  );

  const handleCreateCollection = async () => {
    const name = newCollectionName.trim();
    if (!name) return;
    try {
      const col = await createCollection({ name, description: newCollectionDesc.trim() });
      setCreateCollectionOpen(false);
      setNewCollectionName(""); setNewCollectionDesc("");
      await reloadCollections();
      setSelectedCollectionId(col.id);
      addToast({ type: "success", message: `Collection « ${name} » créée.` });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec de création" });
    }
  };

  const handleCreateFolder = async () => {
    const name = newFolderName.trim();
    if (!name || !selectedCollectionId) return;
    try {
      const folder = await createFolder({
        name,
        parent_id: newFolderParentId,
        collection_id: selectedCollectionId,
      });
      setCreateFolderOpen(false);
      setNewFolderName(""); setNewFolderParentId(null);
      setSelectedFolderId(folder.id);
      const refreshed = await listFolderTree(undefined, selectedCollectionId);
      setTree(refreshed);
      addToast({ type: "success", message: `Dossier « ${name} » créé.` });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec de création" });
    }
  };

  const handleRename = async () => {
    if (!renameTarget) return;
    const name = renameValue.trim();
    if (!name) return;
    try {
      if (renameTarget.kind === "collection") {
        await updateCollection(renameTarget.id, { name });
        await reloadCollections();
      } else {
        await updateFolder(renameTarget.id, { name });
        if (selectedCollectionId) {
          setTree(await listFolderTree(undefined, selectedCollectionId));
        }
      }
      setRenameTarget(null);
      addToast({ type: "success", message: "Renommé." });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec du renommage" });
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (deleteTarget.kind === "collection") {
        await deleteCollection(deleteTarget.id);
        if (selectedCollectionId === deleteTarget.id) {
          setSelectedCollectionId(null); setSelectedFolderId(null);
        }
        await reloadCollections();
      } else {
        await deleteFolder(deleteTarget.id);
        if (selectedFolderId === deleteTarget.id) setSelectedFolderId(null);
        if (selectedCollectionId) {
          setTree(await listFolderTree(undefined, selectedCollectionId));
        }
      }
      setDeleteTarget(null);
      addToast({ type: "success", message: "Supprimé." });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec de la suppression" });
    }
  };

  // ── Rendu ────────────────────────────────────────────────────────────
  return (
    <div className="flex h-full min-h-0 gap-4">
      {/* Sidebar : collections */}
      <aside className="flex w-64 shrink-0 flex-col gap-2 rounded-xl border border-line-1 bg-bg-1 p-3">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-sm font-semibold">
            <Library size={14} /> Collections
          </span>
          <Button size="sm" variant="ghost" onClick={() => setCreateCollectionOpen(true)} aria-label="Nouvelle collection">
            <Plus size={14} />
          </Button>
        </div>
        {collectionsLoading ? (
          <div className="flex items-center gap-2 px-1 py-2 text-xs text-muted-foreground">
            <Loader2 size={12} className="animate-spin" /> Chargement…
          </div>
        ) : collectionsError ? (
          <div className="flex items-center gap-1.5 px-1 py-2 text-xs text-destructive">
            <AlertCircle size={12} /> {collectionsError}
          </div>
        ) : collections.length === 0 ? (
          <p className="px-1 py-2 text-xs text-muted-foreground">
            Aucune collection. Créez-en une pour organiser vos dossiers.
          </p>
        ) : (
          <div className="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto">
            {collections.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => { setSelectedCollectionId(c.id); setSelectedFolderId(null); }}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-2 py-1.5 text-left text-sm transition-colors",
                  selectedCollectionId === c.id
                    ? "bg-accent/15 text-accent"
                    : "text-foreground-secondary hover:bg-bg-3",
                )}
              >
                <Library size={13} className="shrink-0" />
                <span className="truncate">{c.name}</span>
                <Badge variant="secondary" className="ml-auto shrink-0 text-[10px]">
                  {c.document_ids?.length ?? 0}
                </Badge>
              </button>
            ))}
          </div>
        )}
      </aside>

      {/* Zone principale */}
      <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-3">
        {!selectedCollectionId ? (
          <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-line-1 text-sm text-muted-foreground">
            Sélectionnez une collection pour naviguer dans ses dossiers.
          </div>
        ) : (
          <>
            {/* Fil d'Ariane + actions */}
            <div className="flex flex-wrap items-center gap-2 rounded-xl border border-line-1 bg-bg-1 px-3 py-2">
              <button
                type="button"
                onClick={() => setSelectedFolderId(null)}
                className={cn(
                  "text-sm font-medium transition-colors",
                  selectedFolderId ? "text-foreground-secondary hover:text-accent" : "text-accent",
                )}
              >
                {collectionMeta.collection?.name ?? "…"}
              </button>
              {trail.map((node) => (
                <React.Fragment key={node.id}>
                  <ChevronRight size={12} className="text-muted-foreground" />
                  <button
                    type="button"
                    onClick={() => setSelectedFolderId(node.id)}
                    className={cn(
                      "text-sm transition-colors",
                      selectedFolderId === node.id
                        ? "font-medium text-accent"
                        : "text-foreground-secondary hover:text-accent",
                    )}
                  >
                    {node.name}
                  </button>
                </React.Fragment>
              ))}
              <div className="ml-auto flex items-center gap-1">
                <Button
                  size="sm" variant="ghost"
                  onClick={() => { setNewFolderParentId(selectedFolderId); setCreateFolderOpen(true); }}
                >
                  <FolderPlus size={13} className="mr-1" /> Nouveau dossier
                </Button>
                {selectedFolderId && selectedFolder && (
                  <>
                    <Button size="sm" variant="ghost" aria-label="Renommer le dossier"
                      onClick={() => { setRenameTarget({ kind: "folder", id: selectedFolder.id, name: selectedFolder.name }); setRenameValue(selectedFolder.name); }}>
                      <Pencil size={13} />
                    </Button>
                    <Button size="sm" variant="ghost" aria-label="Supprimer le dossier"
                      onClick={() => setDeleteTarget({ kind: "folder", id: selectedFolder.id, name: selectedFolder.name })}>
                      <Trash2 size={13} className="text-destructive" />
                    </Button>
                  </>
                )}
                {!selectedFolderId && collectionMeta.collection && (
                  <>
                    <Button size="sm" variant="ghost" aria-label="Renommer la collection"
                      onClick={() => { setRenameTarget({ kind: "collection", id: collectionMeta.collection!.id, name: collectionMeta.collection!.name }); setRenameValue(collectionMeta.collection!.name); }}>
                      <Pencil size={13} />
                    </Button>
                    <Button size="sm" variant="ghost" aria-label="Supprimer la collection"
                      onClick={() => setDeleteTarget({ kind: "collection", id: collectionMeta.collection!.id, name: collectionMeta.collection!.name })}>
                      <Trash2 size={13} className="text-destructive" />
                    </Button>
                  </>
                )}
              </div>
            </div>

            <div className="flex min-h-0 flex-1 gap-3">
              {/* Arbre des dossiers */}
              <div className="w-64 shrink-0 overflow-y-auto rounded-xl border border-line-1 bg-bg-1 p-2">
                {treeLoading ? (
                  <div className="flex items-center gap-2 px-2 py-2 text-xs text-muted-foreground">
                    <Loader2 size={12} className="animate-spin" /> Chargement…
                  </div>
                ) : tree.length === 0 ? (
                  <p className="px-2 py-2 text-xs text-muted-foreground">
                    Aucun dossier dans cette collection.
                  </p>
                ) : (
                  tree.map((node) => (
                    <FolderNode
                      key={node.id} node={node} depth={0}
                      selectedId={selectedFolderId}
                      onSelect={setSelectedFolderId}
                    />
                  ))
                )}
              </div>

              {/* Listing des ressources */}
              <div className="min-w-0 flex-1 overflow-y-auto rounded-xl border border-line-1 bg-bg-1 p-3">
                {resourcesLoading ? (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 size={12} className="animate-spin" /> Chargement des ressources…
                  </div>
                ) : selectedFolderId ? (
                  resources.length === 0 ? (
                    <p className="text-xs text-muted-foreground">Aucune ressource classée dans ce dossier.</p>
                  ) : (
                    <ul className="flex flex-col gap-1">
                      {resources.map((r) => (
                        <li key={`${r.resource_type}-${r.resource_id}`}
                          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-bg-3">
                          {r.resource_type === "collection" ? <Library size={14} /> : <FileText size={14} />}
                          <span className="truncate">
                            {String((r.record as Record<string, unknown> | null)?.name
                              ?? (r.record as Record<string, unknown> | null)?.label
                              ?? r.resource_id)}
                          </span>
                          <Badge variant="secondary" className="ml-auto text-[10px]">{r.resource_type}</Badge>
                        </li>
                      ))}
                    </ul>
                  )
                ) : (docs ?? []).length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    Aucun document indexé à la racine de cette collection.
                  </p>
                ) : (
                  <ul className="flex flex-col gap-1">
                    {(docs ?? []).map((d) => (
                      <li key={d.id} className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-bg-3">
                        <FileText size={14} className="shrink-0" />
                        <span className="truncate">{d.title || d.id}</span>
                        <Badge variant="secondary" className="ml-auto shrink-0 text-[10px]">
                          {d.chunks.length} chunk{d.chunks.length > 1 ? "s" : ""}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                )}
                {docs && docs.length > 0 && !selectedFolderId && (
                  <p className="mt-3 flex items-center gap-1 text-[11px] text-muted-foreground">
                    <ImageIcon size={11} /> Les images importées apparaîtront ici lors de la phase ressources.
                  </p>
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Dialogs (opérations courtes) */}
      <Dialog open={createCollectionOpen} onClose={() => setCreateCollectionOpen(false)} title="Nouvelle collection" size="sm">
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label htmlFor="kb-col-name" className="mb-1 block text-sm font-medium">Nom</label>
            <Input id="kb-col-name" value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)} placeholder="ex: OSINT" />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="kb-col-desc" className="mb-1 block text-sm font-medium">Description</label>
            <Textarea id="kb-col-desc" rows={2} value={newCollectionDesc}
              onChange={(e) => setNewCollectionDesc(e.target.value)} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCreateCollectionOpen(false)}>Annuler</Button>
            <Button disabled={!newCollectionName.trim()} onClick={() => void handleCreateCollection()}>Créer</Button>
          </div>
        </div>
      </Dialog>

      <Dialog open={createFolderOpen} onClose={() => setCreateFolderOpen(false)} title="Nouveau dossier" size="sm">
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label htmlFor="kb-folder-name" className="mb-1 block text-sm font-medium">Nom du dossier</label>
            <Input id="kb-folder-name" value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder={newFolderParentId ? "Sous-dossier du dossier sélectionné" : "Dossier racine de la collection"} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCreateFolderOpen(false)}>Annuler</Button>
            <Button disabled={!newFolderName.trim()} onClick={() => void handleCreateFolder()}>Créer</Button>
          </div>
        </div>
      </Dialog>

      <Dialog open={renameTarget !== null} onClose={() => setRenameTarget(null)}
        title={renameTarget?.kind === "collection" ? "Renommer la collection" : "Renommer le dossier"} size="sm">
        <div className="flex flex-col gap-3">
          <Input value={renameValue} onChange={(e) => setRenameValue(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setRenameTarget(null)}>Annuler</Button>
            <Button disabled={!renameValue.trim()} onClick={() => void handleRename()}>Renommer</Button>
          </div>
        </div>
      </Dialog>

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title={deleteTarget?.kind === "collection" ? "Supprimer la collection" : "Supprimer le dossier"}
        message={
          deleteTarget?.kind === "collection"
            ? `Supprimer « ${deleteTarget?.name} » ? Les documents indexés restent dans le catalogue RAG.`
            : `Supprimer « ${deleteTarget?.name} » ? Les sous-dossiers remontent d'un niveau ; les ressources classées ne sont pas supprimées.`
        }
        confirmLabel="Supprimer"
        onConfirm={() => void handleDelete()}
      />
    </div>
  );
}

