"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  ScanSearch,
  Trash2,
  Archive,
  GitMerge,
  RefreshCw,
  Copy,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
} from "lucide-react";
import {
  scanDuplicates,
  resolveDuplicateGroup,
  getDedupCategories,
  type DuplicateReport,
  type DuplicateGroup,
  type DuplicateAction,
  type ResolutionResult,
  type DuplicateCategory,
} from "@/lib/api/dedup";

const CATEGORY_LABELS: Record<DuplicateCategory, string> = {
  exact_duplicate: "Exact duplicates",
  probable_duplicate: "Probable duplicates",
  same_name_different_content: "Same name, different content",
  different_version: "Different versions",
  same_content_different_location: "Same content, different location",
  already_indexed: "Already indexed",
  orphan_document: "Orphan documents",
  broken_reference: "Broken references",
};

const CATEGORY_ICONS: Record<DuplicateCategory, React.ReactNode> = {
  exact_duplicate: <Copy className="h-4 w-4" />,
  probable_duplicate: <Copy className="h-4 w-4 text-yellow-400" />,
  same_name_different_content: <AlertTriangle className="h-4 w-4 text-orange-400" />,
  different_version: <RefreshCw className="h-4 w-4 text-blue-400" />,
  same_content_different_location: <ScanSearch className="h-4 w-4 text-purple-400" />,
  already_indexed: <CheckCircle2 className="h-4 w-4 text-green-400" />,
  orphan_document: <AlertTriangle className="h-4 w-4 text-red-400" />,
  broken_reference: <ShieldAlert className="h-4 w-4 text-red-500" />,
};

const ACTION_LABELS: Record<DuplicateAction, string> = {
  keep_both: "Keep both",
  replace_with_newest: "Replace with newest",
  keep_primary: "Keep primary",
  move_to_archive: "Move to archive",
  delete_after_confirm: "Delete",
  repair_reference: "Repair reference",
  merge_associations: "Merge associations",
};

export function DedupWorkspace() {
  const queryClient = useQueryClient();
  const [activeReport, setActiveReport] = React.useState<DuplicateReport | null>(null);
  const [resolvingGroup, setResolvingGroup] = React.useState<DuplicateGroup | null>(null);
  const [lastResult, setLastResult] = React.useState<ResolutionResult | null>(null);

  const categoriesQuery = useQuery({ queryKey: ["dedup-categories"], queryFn: getDedupCategories });

  const scanMutation = useMutation({
    mutationFn: () => scanDuplicates(),
    onSuccess: (report) => {
      setActiveReport(report);
      queryClient.setQueryData(["dedup-report", report.scan_id], report);
    },
  });

  const resolveMutation = useMutation({
    mutationFn: ({ group, action, confirmed, primaryItemId }: {
      group: DuplicateGroup; action: DuplicateAction; confirmed: boolean; primaryItemId: string;
    }) => resolveDuplicateGroup(group.group_id, action, confirmed, primaryItemId),
    onSuccess: (result) => {
      setLastResult(result);
      if (result.status === "needs_confirm") {
        return;
      }
      // Refresh report after successful resolution
      scanMutation.mutate();
    },
  });

  const handleResolve = (group: DuplicateGroup, action: DuplicateAction, primaryItemId = "") => {
    resolveMutation.mutate({ group, action, confirmed: false, primaryItemId });
  };

  const handleConfirmDelete = (group: DuplicateGroup) => {
    resolveMutation.mutate({ group, action: "delete_after_confirm", confirmed: true, primaryItemId: "" });
  };

  const groups = activeReport?.groups ?? [];
  const orphans = activeReport?.orphans ?? [];
  const broken = activeReport?.broken_references ?? [];
  return (
    <div className="flex h-full min-w-0 flex-col">
      <div className="flex items-center justify-between border-b border-line-1 px-6 py-4" style={{ background: "var(--panel)" }}>
        <div>
          <h1 className="text-lg font-semibold text-foreground">Duplicate Detection</h1>
          <p className="text-sm text-muted-foreground">
            Scan Library, Projects and Knowledge for duplicates. No file is ever deleted automatically.
          </p>
        </div>
        <Button onClick={() => scanMutation.mutate()} disabled={scanMutation.isPending} size="sm">
          {scanMutation.isPending ? <><Spinner className="h-4 w-4 mr-2" />Scanning...</> : <><ScanSearch className="h-4 w-4 mr-2" />Scan</>}
        </Button>
      </div>

      {lastResult && (
        <div className={`mx-6 mt-4 flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${lastResult.status === "applied" ? "border-green-500/30 bg-green-500/10 text-green-400" : lastResult.status === "needs_confirm" ? "border-yellow-500/30 bg-yellow-500/10 text-yellow-400" : "border-red-500/30 bg-red-500/10 text-red-400"}`}>
          {lastResult.status === "needs_confirm" ? <AlertTriangle className="h-4 w-4" /> : lastResult.status === "applied" ? <CheckCircle2 className="h-4 w-4" /> : <ShieldAlert className="h-4 w-4" />}
          <span>{lastResult.message || lastResult.status}</span>
          {lastResult.status === "needs_confirm" && resolvingGroup && (
            <Button size="sm" variant="destructive" className="ml-auto" onClick={() => handleConfirmDelete(resolvingGroup)}>
              Confirm delete
            </Button>
          )}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6">
        {!activeReport && !scanMutation.isPending && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-muted-foreground">
            <ScanSearch className="h-12 w-12 opacity-40" />
            <p className="text-sm">Run a scan to detect duplicate resources across Library, Projects and Knowledge.</p>
          </div>
        )}

        {scanMutation.isPending && <div className="flex items-center gap-2 text-muted-foreground"><Spinner className="h-5 w-5" /><span>Scanning all domains...</span></div>}

        {activeReport && (
          <div className="space-y-6">
            <div className="flex gap-4 text-sm">
              <span className="rounded-md bg-[var(--accent)]/10 px-3 py-1 font-medium text-foreground">{activeReport.total_scanned} scanned</span>
              <span className="text-muted-foreground">{activeReport.total_files} files</span>
              <span className="text-muted-foreground">{activeReport.total_rag_documents} RAG docs</span>
              <span className="text-muted-foreground">{groups.length} groups</span>
            </div>

            {groups.map((group) => (
              <div key={group.group_id} className="rounded-lg border border-line-1" style={{ background: "var(--panel)" }}>
                <div className="flex items-center gap-2 border-b border-line-1 px-4 py-2">
                  {CATEGORY_ICONS[group.category]}
                  <span className="text-sm font-medium text-foreground">{CATEGORY_LABELS[group.category]}</span>
                  <span className="ml-auto text-xs text-muted-foreground">{group.items.length} items</span>
                </div>
                <div className="divide-y divide-line-1">
                  {group.items.map((item) => (
                    <div key={item.id} className="flex items-center gap-3 px-4 py-2 text-sm">
                      <span className="flex-1 truncate text-foreground">{item.name}</span>
                      <span className="text-xs text-muted-foreground">{item.domain}</span>
                      {item.locations[0] && <span className="max-w-[200px] truncate text-xs text-muted-foreground">{item.locations[0]}</span>}
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2 border-t border-line-1 px-4 py-2">
                  <Button size="sm" variant="ghost" onClick={() => handleResolve(group, "keep_both")}>Keep both</Button>
                  <Button size="sm" variant="ghost" onClick={() => handleResolve(group, "replace_with_newest")}>Keep newest</Button>
                  <Button size="sm" variant="ghost" onClick={() => { setResolvingGroup(group); handleResolve(group, "delete_after_confirm"); }}><Trash2 className="h-3 w-3 mr-1" />Delete</Button>
                  <Button size="sm" variant="ghost" onClick={() => handleResolve(group, "merge_associations")}><GitMerge className="h-3 w-3 mr-1" />Merge</Button>
                  <Button size="sm" variant="ghost" onClick={() => handleResolve(group, "move_to_archive")}><Archive className="h-3 w-3 mr-1" />Archive</Button>
                </div>
              </div>
            ))}

            {orphans.length > 0 && (
              <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-4 text-sm">
                <p className="font-medium text-yellow-400">{orphans.length} orphan document(s) (RAG without source file)</p>
              </div>
            )}
            {broken.length > 0 && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-sm">
                <p className="font-medium text-red-400">{broken.length} broken reference(s)</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
