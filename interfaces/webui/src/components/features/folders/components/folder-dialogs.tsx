"use client";

/**
 * FolderDialogs — création, renommage, suppression, déplacement.
 *
 * Consomme l'état de dialog fourni par le FolderTree (source unique des
 * actions) et transmet les intentions au Core via /v1/folders.
 */

import * as React from "react";
import { Folder, Move } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import type { FolderTree } from "@/lib/api/folders";
import type { FolderDialogState } from "./folder-tree";

const INDENT = 12;

export interface FolderDialogsCallbacks {
  createFolder: (data: { name: string; parent_id?: string | null }) => void;
  updateFolder: (data: { folderId: string; name: string }) => void;
  deleteFolder: (id: string) => void;
  moveFolder: (data: { folderId: string; parentId: string | null }) => void;
}

interface FolderDialogsProps extends FolderDialogsCallbacks {
  dialog: FolderDialogState;
  tree: FolderTree[];
  currentName: string;
  onClose: () => void;
}

export function FolderDialogs({
  dialog, tree, currentName, onClose,
  createFolder, updateFolder, deleteFolder, moveFolder,
}: FolderDialogsProps) {
  const [name, setName] = React.useState("");
  const dialogNodeKey = dialog && "nodeId" in dialog ? dialog.nodeId : "";

  React.useEffect(() => {
    if (dialog?.kind === "rename") setName(currentName);
    else if (dialog?.kind === "create") setName("");
  }, [dialog?.kind, dialogNodeKey, currentName]);

  const flat: { id: string; name: string; depth: number }[] = [];
  const walk = (nodes: FolderTree[], depth: number) => {
    for (const n of nodes) {
      flat.push({ id: n.id, name: n.name, depth });
      walk(n.children, depth + 1);
    }
  };
  walk(tree, 0);

  const target =
    dialog && dialog.kind !== "create" && dialog.kind !== null
      ? flat.find((f) => f.id === dialog.nodeId)
      : undefined;
  const nodeName =
    dialog?.kind === "create"
      ? (dialog.parentId && flat.find((f) => f.id === dialog.parentId)?.name) || "racine"
      : target?.name ?? "";

  const isNameDialog = dialog?.kind === "create" || dialog?.kind === "rename";

  const submitName = () => {
    if (!name.trim() || !dialog) return;
    if (dialog.kind === "create") createFolder({ name: name.trim(), parent_id: dialog.parentId });
    else if (dialog.kind === "rename") updateFolder({ folderId: dialog.nodeId, name: name.trim() });
    onClose();
  };

  return (
    <>
      {/* Créer / Renommer (saisie de nom) */}
      <Dialog
        open={isNameDialog}
        onOpenChange={(o) => !o && onClose()}
        title={
          dialog?.kind === "create"
            ? dialog.parentId
              ? `Nouveau sous-dossier (dans « ${nodeName} »)`
              : "Nouveau dossier"
            : `Renommer « ${nodeName} »`
        }
      >
        <div className="space-y-3">
          <Input
            autoFocus
            placeholder="Nom du dossier (libre)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submitName()}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={onClose}>Annuler</Button>
            <Button size="sm" disabled={!name.trim()} onClick={submitName}>
              {dialog?.kind === "create" ? "Créer" : "Renommer"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Déplacer */}
      <Dialog
        open={dialog?.kind === "move"}
        onOpenChange={(o) => !o && onClose()}
        title={`Déplacer « ${nodeName} »`}
      >
        <div className="max-h-72 overflow-y-auto space-y-1">
          <button
            type="button"
            className="w-full flex items-center gap-1.5 rounded px-2 py-1.5 text-sm hover:bg-muted/60 text-left"
            onClick={() => {
              if (dialog?.kind === "move") moveFolder({ folderId: dialog.nodeId, parentId: null });
              onClose();
            }}
          >
            <Move size={14} /> Racine (hors dossier)
          </button>
          {flat
            .filter((f) => dialog?.kind === "move" && f.id !== dialog.nodeId)
            .map((f) => (
              <button
                key={f.id}
                type="button"
                className="w-full flex items-center gap-1.5 rounded px-2 py-1.5 text-sm hover:bg-muted/60 text-left"
                style={{ paddingLeft: `${8 + f.depth * INDENT}px` }}
                onClick={() => {
                  if (dialog?.kind === "move") moveFolder({ folderId: dialog.nodeId, parentId: f.id });
                  onClose();
                }}
              >
                <Folder size={14} /> {f.name}
              </button>
            ))}
        </div>
        <div className="flex justify-end pt-3">
          <Button variant="ghost" size="sm" onClick={onClose}>Annuler</Button>
        </div>
      </Dialog>

      {/* Supprimer */}
      <ConfirmDialog
        open={dialog?.kind === "delete"}
        onOpenChange={(o) => !o && onClose()}
        title={`Supprimer « ${nodeName} » ?`}
        message="Les sous-dossiers seront re-rattachés au parent. Les ressources classées sont conservées (seul le classement est retiré)."
        confirmLabel="Supprimer"
        destructive
        onConfirm={() => {
          if (dialog?.kind === "delete") deleteFolder(dialog.nodeId);
          onClose();
        }}
      />
    </>
  );
}