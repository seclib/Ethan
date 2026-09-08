"use client";

/**
 * ClassifyDialog — classe une ressource (knowledge / collection / skill)
 * dans un ou plusieurs dossiers (multi-membership).
 *
 * La liste des dossiers actuels provient du folderIndex Core (cache batch)
 * ; la mutation de remplacement est déléguée à POST /v1/folders/move-resource.
 * Aucune logique métier ici : uniquement la sélection utilisateur.
 */

import * as React from "react";
import { Folder, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import { useResourceClassification } from "../hooks/use-folder-resources";
import type { FolderTree, FolderResourceType } from "@/lib/api/folders";

export interface ClassifyTarget {
  resourceType: FolderResourceType;
  resourceId: string;
  resourceName: string;
}

const INDENT = 12;

interface ClassifyDialogProps {
  target: ClassifyTarget;
  tree: FolderTree[];
  /** Index `{resource_id: [folder_id, ...]}` (cache Core, batch). */
  folderIndex: Record<string, string[]>;
  onClose: () => void;
}

export function ClassifyDialog({ target, tree, folderIndex, onClose }: ClassifyDialogProps) {
  const classification = useResourceClassification();
  const current = folderIndex[target.resourceId] ?? [];
  const [selected, setSelected] = React.useState<Set<string>>(() => new Set(current));

  const flat: { id: string; name: string; depth: number }[] = [];
  const walk = (nodes: FolderTree[], depth: number) => {
    for (const n of nodes) {
      flat.push({ id: n.id, name: n.name, depth });
      walk(n.children, depth + 1);
    }
  };
  walk(tree, 0);

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const submit = () => {
    classification.moveResource({
      resourceType: target.resourceType,
      resourceId: target.resourceId,
      folderIds: [...selected],
    });
    onClose();
  };

  const unchanged = current.length === selected.size && current.every((id) => selected.has(id));

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()} title={`Classer « ${target.resourceName} »`}>
      <div className="space-y-3">
        <p className="text-xs text-muted-foreground">
          Dossiers (multisélection — un dossier vide n&apos;équivaut pas à une suppression) : cochez les contenants.
        </p>

        {tree.length === 0 ? (
          <div className="py-6 flex justify-center"><Spinner /></div>
        ) : flat.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            Aucun dossier — créez d&apos;abord un dossier dans l&apos;arborescence.
          </p>
        ) : (
          <div className="space-y-0.5 max-h-72 overflow-y-auto">
            {flat.map((f) => {
              const checked = selected.has(f.id);
              return (
                <button
                  key={f.id}
                  type="button"
                  className={`w-full flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted/60 text-left ${
                    checked ? "bg-primary/10 text-primary" : ""
                  }`}
                  style={{ paddingLeft: `${8 + f.depth * INDENT}px` }}
                  onClick={() => toggle(f.id)}
                >
                  <span className="h-4 w-4 grid place-items-center rounded border shrink-0 border-muted-foreground/40">
                    {checked && <Check size={12} />}
                  </span>
                  <Folder size={14} />
                  <span className="truncate flex-1">{f.name}</span>
                </button>
              );
            })}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={onClose}>Annuler</Button>
          <Button size="sm" disabled={unchanged || classification.isMutating} onClick={submit}>
            {classification.isMutating ? <Spinner /> : null} Enregistrer
          </Button>
        </div>
      </div>
    </Dialog>
  );
}