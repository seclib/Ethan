"use client";

/**
 * Contents liés à un dossier — liste des ressources d'un dossier,
 * ressources sans dossier, et liste filtrée par type.  Le classement est
 * délégué au ClassifyDialog (voir folders-workspace.tsx).
 */

import * as React from "react";
import { Database, Sparkles, Layers, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useFolderResources, useUntaggedResources } from "../hooks/use-folder-resources";
import { useFolders } from "../hooks/use-folders";
import { DestinationPickDialog } from "./consolidate-dialogs";
import type { FolderOperationReport } from "@/lib/api/folders";
import type { ClassifyTarget } from "./classify-dialog";
import type { FolderResource, FolderResourceType } from "@/lib/api/folders";

const TYPE_LABELS: Record<FolderResourceType, string> = {
  knowledge: "Knowledge",
  collection: "Collections",
  skill: "Skills",
};

const TYPE_ICONS: Record<FolderResourceType, React.ReactNode> = {
  knowledge: <Database size={14} />,
  collection: <Layers size={14} />,
  skill: <Sparkles size={14} />,
};

// Petit pont d'export pour éviter de dupliquer les labels dans workspace.
export const FOLDER_TYPE_LABELS = TYPE_LABELS;
export const FOLDER_TYPE_ICONS = TYPE_ICONS;

export function FolderContent({
  folderId, typeFilter, onClassify,
}: {
  folderId: string;
  typeFilter: FolderResourceType | null;
  onClassify: (target: ClassifyTarget) => void;
}) {
  const { data: resources = [], isLoading } = useFolderResources(folderId);
  const filtered = typeFilter ? resources.filter((r) => r.resource_type === typeFilter) : resources;

  if (isLoading) {
    return <div className="py-8 flex justify-center"><Spinner /></div>;
  }

  if (filtered.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto border rounded-lg bg-card grid place-items-center">
        <p className="p-6 text-sm text-muted-foreground">
          {typeFilter
            ? `Aucune ressource ${TYPE_LABELS[typeFilter]} dans ce dossier.`
            : "Ce dossier est vide — classez des ressources depuis leurs listes."}
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto border rounded-lg bg-card">
      <ResourceList resources={filtered} onClassify={onClassify} />
    </div>
  );
}

export function UntaggedContent({
  typeFilter, onClassify,
}: {
  typeFilter: FolderResourceType | null;
  onClassify: (target: ClassifyTarget) => void;
}) {
  const [localType, setLocalType] = React.useState<FolderResourceType | null>(null);
  const effectiveType = typeFilter ?? localType;
  const { data: untagged = [], isLoading } = useUntaggedResources(effectiveType);

  return (
    <div className="flex-1 overflow-y-auto border rounded-lg bg-card flex flex-col min-h-0">
      {effectiveType === null && (
        <div className="p-4 flex gap-2 flex-wrap border-b">
          <span className="text-xs text-muted-foreground self-center">Choisissez un type :</span>
          {(Object.keys(TYPE_LABELS) as FolderResourceType[]).map((t) => (
            <Button key={t} variant="outline" size="sm" onClick={() => setLocalType(t)}>
              {TYPE_ICONS[t]} {TYPE_LABELS[t]}
            </Button>
          ))}
        </div>
      )}
      {isLoading ? (
        <div className="py-8 flex justify-center"><Spinner /></div>
      ) : effectiveType === null ? (
        <p className="p-6 text-sm text-muted-foreground">Sélectionnez un type pour lister les ressources sans dossier.</p>
      ) : untagged.length === 0 ? (
        <p className="p-6 text-sm text-muted-foreground">Aucune ressource {TYPE_LABELS[effectiveType]} sans dossier.</p>
      ) : (
        <ul className="divide-y">
          {untagged.map((record) => (
            <li key={record.id as string} className="flex items-center justify-between px-4 py-2.5 text-sm hover:bg-muted">
              <span className="flex items-center gap-2 min-w-0">
                {TYPE_ICONS[effectiveType]}
                <span className="truncate">
                  {nameOrId(record)}
                </span>
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  onClassify({
                    resourceType: effectiveType,
                    resourceId: record.id as string,
                    resourceName: nameOrId(record),
                  })
                }
              >
                Classer
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ResourceList({
  resources,
  onClassify,
}: {
  resources: FolderResource[];
  onClassify: (target: ClassifyTarget) => void;
}) {
  const [selected, setSelected] = React.useState<Set<string>>(new Set());

  const keyOf = (item: FolderResource) => `${item.resource_type}:${item.resource_id}`;

  const toggle = (key: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  const selectedItems = resources.filter((item) => selected.has(keyOf(item)));

  return (
    <div className="flex flex-col min-h-0">
      {selected.size > 0 && (
        <div className="flex items-center gap-2 border-b px-4 py-2 text-sm">
          <span className="font-medium text-muted-foreground">{selected.size} sélectionnée(s)</span>
          <FolderConsolidationActions items={selectedItems} onDone={() => setSelected(new Set())} />
        </div>
      )}
      <ul className="divide-y overflow-y-auto">
        {resources.map((item) => {
          const record = item.record ?? {};
          const name = nameOrId(record) || item.resource_id;
          const key = keyOf(item);
          return (
            <li key={key} className="flex items-center justify-between gap-2 px-4 py-2.5 text-sm hover:bg-muted">
              <span className="flex items-center gap-2 min-w-0">
                <input
                  type="checkbox"
                  aria-label={`Sélectionner ${name}`}
                  checked={selected.has(key)}
                  onChange={() => toggle(key)}
                />
                {TYPE_ICONS[item.resource_type]}
                <span className="truncate">{name}</span>
                <span className="text-xs text-muted-foreground shrink-0">{TYPE_LABELS[item.resource_type]}</span>
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  onClassify({
                    resourceType: item.resource_type,
                    resourceId: item.resource_id,
                    resourceName: name,
                  })
                }
              >
                Classer / déplacer
              </Button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/** Barre d'actions de consolidation pour une sélection de ressources. */
function FolderConsolidationActions({
  items,
  onDone,
}: {
  items: FolderResource[];
  onDone: () => void;
}) {
  const folders = useFolders();
  const [dialog, setDialog] = React.useState<{ mode: "copy" | "move"; report: FolderOperationReport | null } | null>(null);

  const refs = items.map((i) => ({
    resource_type: i.resource_type as FolderResourceType,
    resource_id: i.resource_id,
  }));

  return (
    <>
      <div className="ml-auto flex items-center gap-1.5">
        <Button size="sm" variant="outline" onClick={() => setDialog({ mode: "move", report: null })}>
          Déplacer
        </Button>
        <Button size="sm" variant="outline" onClick={() => setDialog({ mode: "copy", report: null })}>
          Copier
        </Button>
      </div>
      {dialog && (
        <DestinationPickDialog
          tree={folders.tree}
          mode={dialog.mode}
          itemCount={items.length}
          report={dialog.report}
          onConfirm={(targetId) => {
            const run =
              dialog.mode === "copy" ? folders.copyResources : folders.moveResources;
            run({ items: refs, targetId } as never);
            onDone();
            setDialog(null);
          }}
          onClose={() => setDialog(null)}
        />
      )}
    </>
  );
}

export function EmptyState() {
  return (
    <div className="flex-1 min-h-[30vh] grid place-items-center border rounded-lg bg-card">
      <div className="text-center p-8 max-w-sm">
        <FolderOpen size={40} className="mx-auto mb-3 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          Sélectionnez un dossier dans l&apos;arbre pour voir ses ressources, ou « Sans dossier »
          pour classer les ressources non organisées.
        </p>
      </div>
    </div>
  );
}

function nameOrId(record: Record<string, unknown>): string {
  return (
    (record.name as string) ||
    (record.title as string) ||
    (record.label as string) ||
    (record.id as string) ||
    ""
  );
}
