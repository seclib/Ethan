"use client";

/**
 * FolderTree — arborescence interactive des dossiers utilisateur.
 *
 * Rendu récursif de la hiérarchie libre (aucune catégorie imposée par ETHAN).
 * Interactions : sélection, création (racine ou sous-dossier), renommage,
 * suppression, déplacement (re-parentage).  Toutes les mutations passent par
 * /v1/folders — ce composant ne possède aucun état métier.
 */

import * as React from "react";
import {
  ChevronRight, ChevronDown, Folder, FolderOpen,
  Plus, Pencil, Trash2, Move,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { FolderTree } from "@/lib/api/folders";

const INDENT = 12;

export interface FolderTreeCallbacks {
  createFolder: (data: { name: string; parent_id?: string | null }) => void;
  updateFolder: (data: { folderId: string; name: string }) => void;
  deleteFolder: (id: string) => void;
  moveFolder: (data: { folderId: string; parentId: string | null }) => void;
}

export type FolderDialogState =
  | { kind: "create"; parentId: string | null }
  | { kind: "rename"; nodeId: string }
  | { kind: "delete"; nodeId: string }
  | { kind: "move"; nodeId: string }
  | null;

interface FolderTreeProps {
  tree: FolderTree[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onDialogChange: (dialog: FolderDialogState) => void;
  onCreateRoot: () => void;
}

export function FolderTree({
  tree, selectedId, onSelect, onDialogChange, onCreateRoot,
}: FolderTreeProps) {
  const [expanded, setExpanded] = React.useState<Set<string>>(new Set());

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const renderNode = (node: FolderTree, depth: number) => {
    const isExpanded = expanded.has(node.id);
    const isSelected = selectedId === node.id;
    const hasChildren = node.children.length > 0;
    return (
      <div key={node.id}>
        <div
          className={`group flex items-center gap-1 rounded-md pl-2 pr-1 py-1 text-sm cursor-pointer transition-colors ${
            isSelected ? "bg-primary/10 text-primary font-medium" : "hover:bg-muted/60"
          }`}
          style={{ marginLeft: depth * INDENT }}
          onClick={() => onSelect(node.id)}
        >
          <button
            type="button"
            className="h-4 w-4 shrink-0 grid place-items-center text-muted-foreground"
            onClick={(e) => {
              e.stopPropagation();
              if (hasChildren) toggle(node.id);
            }}
            aria-label={isExpanded ? "Réduire" : "Déplier"}
          >
            {hasChildren && (isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />)}
          </button>
          {isSelected ? <FolderOpen size={14} /> : <Folder size={14} />}
          <span className="flex-1 truncate">{node.name}</span>
          {node.resource_count > 0 && (
            <span className="rounded-full bg-muted px-1.5 text-[10px] text-muted-foreground">{node.resource_count}</span>
          )}
          <span className="hidden group-hover:flex items-center">
            <button
              type="button"
              className="h-5 w-5 grid place-items-center rounded hover:bg-muted"
              title="Créer un sous-dossier"
              onClick={(e) => {
                e.stopPropagation();
                onDialogChange({ kind: "create", parentId: node.id });
              }}
            >
              <Plus size={12} />
            </button>
          </span>
        </div>
        {isExpanded && hasChildren && node.children.map((child) => renderNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <>
      <div className="flex items-center justify-between px-1 pb-2">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Dossiers</span>
        <Button variant="ghost" size="sm" onClick={onCreateRoot}>
          <Plus size={14} /> Nouveau
        </Button>
      </div>

      <div className="space-y-0.5">
        {tree.map((node) => renderNode(node, 0))}
        {tree.length === 0 && (
          <p className="px-2 py-4 text-xs text-muted-foreground text-center">
            Aucun dossier — créez votre première organisation (ex. OSINT, Code, Forensic…).
          </p>
        )}
      </div>

      {selectedId && (
        <div className="flex items-center gap-1 px-1 pt-2 mt-2 border-t">
          <Button variant="ghost" size="sm" className="text-xs" onClick={() => onDialogChange({ kind: "rename", nodeId: selectedId })}>
            <Pencil size={13} /> Renommer
          </Button>
          <Button variant="ghost" size="sm" className="text-xs" onClick={() => onDialogChange({ kind: "move", nodeId: selectedId })}>
            <Move size={13} /> Déplacer
          </Button>
          <Button variant="ghost" size="sm" className="text-xs text-destructive" onClick={() => onDialogChange({ kind: "delete", nodeId: selectedId })}>
            <Trash2 size={13} /> Supprimer
          </Button>
        </div>
      )}
    </>
  );
}