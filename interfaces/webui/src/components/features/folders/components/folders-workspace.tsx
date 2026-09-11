"use client";

/**
 * FoldersWorkspace — cockpit d'organisation des ressources ETHAN.
 *
 * Gauche : arborescence des dossiers (navigation, création, renommage,
 * suppression, déplacement).  Droite : ressources du dossier sélectionné
 * (filtrables par type) ou ressources sans dossier.  Le classement réel
 * (attach/detach/move) est délégué au Core via /v1/folders — cette vue ne
 * détient aucun état métier.
 */

import * as React from "react";
import { Inbox, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useFolders, useFoldersNavigation } from "../hooks/use-folders";
import { FolderTree, type FolderDialogState } from "./folder-tree";
import { FolderDialogs } from "./folder-dialogs";
import { MergeFoldersDialog } from "./consolidate-dialogs";
import { FolderContent, UntaggedContent, EmptyState, FOLDER_TYPE_LABELS, FOLDER_TYPE_ICONS } from "./folder-contents";
import { ClassifyDialog, type ClassifyTarget } from "./classify-dialog";
import type { FolderResourceType, FolderTree as FolderTreeNode } from "@/lib/api/folders";

export function FoldersWorkspace() {
  const folders = useFolders();
  const nav = useFoldersNavigation();

  const [dialog, setDialog] = React.useState<FolderDialogState>(null);
  const [classifyTarget, setClassifyTarget] = React.useState<ClassifyTarget | null>(null);

  const tree = folders.tree;
  const currentName = React.useMemo(() => {
    const flat: { id: string; name: string }[] = [];
    const walk = (nodes: FolderTreeNode[]) => {
      for (const n of nodes) {
        flat.push({ id: n.id, name: n.name });
        walk(n.children);
      }
    };
    walk(tree);
    return flat.find((f) => f.id === nav.selectedFolderId)?.name ?? "";
  }, [tree, nav.selectedFolderId]);

  return (
    <div className="flex h-full min-h-0 gap-4">
      <aside className="w-64 shrink-0 min-h-0 overflow-y-auto border rounded-lg bg-card p-2 flex flex-col">
        {folders.treeLoading ? (
          <div className="py-8 flex justify-center"><Spinner /></div>
        ) : (
          <>
            <FolderTree
              tree={folders.tree}
              selectedId={nav.selectedFolderId}
              onSelect={(id) => {
                nav.setSelectedFolderId(id);
                nav.setShowUntagged(false);
                nav.setTypeFilter(null);
              }}
              onDialogChange={setDialog}
              onCreateRoot={() => setDialog({ kind: "create", parentId: null })}
            />
            <button
              type="button"
              className={`mt-2 flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted ${
                nav.showUntagged ? "bg-primary/10 text-primary font-medium" : ""
              }`}
              onClick={() => {
                nav.setShowUntagged(true);
                nav.setSelectedFolderId(null);
              }}
            >
              <Inbox size={14} /> Sans dossier
            </button>
            <button
              type="button"
              className="mt-2 flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted"
              onClick={() => setDialog({ kind: "merge" })}
            >
              <Layers size={14} /> Fusionner des dossiers…
            </button>
          </>
        )}
        <FolderDialogs
          dialog={dialog}
          tree={folders.tree}
          currentName={currentName}
          onClose={() => setDialog(null)}
          createFolder={folders.createFolder}
          updateFolder={({ folderId, name }) => folders.updateFolder({ folderId, data: { name } })}
          deleteFolder={(id) => folders.deleteFolder(id)}
          moveFolder={folders.moveFolder}
        />
        {dialog?.kind === "merge" && (
          <MergeFoldersDialog
            tree={folders.tree}
            onMerge={(folderIds, targetId, removeSources) =>
              folders.mergeFolders({ folderIds, targetId, removeSources })
            }
            onClose={() => setDialog(null)}
          />
        )}
      </aside>

      <section className="flex-1 min-w-0 min-h-0 flex flex-col gap-3">
        <div className="flex items-center gap-1.5 flex-wrap">
          <Button
            variant={nav.typeFilter === null ? "secondary" : "ghost"}
            size="sm"
            onClick={() => nav.setTypeFilter(null)}
          >
            Tous les types
          </Button>
          {(Object.keys(FOLDER_TYPE_LABELS) as FolderResourceType[]).map((t) => (
            <Button
              key={t}
              variant={nav.typeFilter === t ? "secondary" : "ghost"}
              size="sm"
              onClick={() => nav.setTypeFilter(t)}
            >
              {FOLDER_TYPE_ICONS[t]} {FOLDER_TYPE_LABELS[t]}
            </Button>
          ))}
        </div>

        {nav.selectedFolderId ? (
          <FolderContent
            folderId={nav.selectedFolderId}
            typeFilter={nav.typeFilter}
            onClassify={setClassifyTarget}
          />
        ) : nav.showUntagged ? (
          <UntaggedContent
            typeFilter={nav.typeFilter}
            onClassify={setClassifyTarget}
          />
        ) : (
          <EmptyState />
        )}
      </section>

      {classifyTarget && (
        <ClassifyDialog
          target={classifyTarget}
          tree={folders.tree}
          folderIndex={folders.folderIndex}
          onClose={() => setClassifyTarget(null)}
        />
      )}
    </div>
  );
}