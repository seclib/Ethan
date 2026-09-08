"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { getLibrary, type LibraryItem, type LibraryItemType, type LibraryFilters } from "@/lib/api/library";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Search, FileText, Image, BookOpen, FolderOpen, LayoutGrid, List, SortAsc, SortDesc, Loader2, AlertCircle } from "lucide-react";

const TYPE_CONFIG: Record<LibraryItemType, { icon: React.ReactNode; color: string }> = {
  document: { icon: <FileText className="h-4 w-4" />, color: "text-blue-400" },
  image: { icon: <Image className="h-4 w-4" />, color: "text-green-400" },
  knowledge: { icon: <BookOpen className="h-4 w-4" />, color: "text-purple-400" },
  collection: { icon: <FolderOpen className="h-4 w-4" />, color: "text-yellow-400" },
  project: { icon: <FolderOpen className="h-4 w-4" />, color: "text-orange-400" },
};

const TYPE_FILTERS: { id: LibraryItemType | "all"; label: string }[] = [
  { id: "all", label: "All" },
  { id: "document", label: "Documents" },
  { id: "image", label: "Images" },
  { id: "knowledge", label: "Knowledge" },
  { id: "collection", label: "Collections" },
];

export function LibraryWorkspace() {
  const [search, setSearch] = React.useState("");
  const [typeFilter, setTypeFilter] = React.useState<LibraryItemType | "all">("all");
  const [sortBy, setSortBy] = React.useState<LibraryFilters["sort_by"]>("created_at");
  const [sortOrder, setSortOrder] = React.useState<LibraryFilters["sort_order"]>("desc");
  const [viewMode, setViewMode] = React.useState<"grid" | "list">("grid");
  const [selectedItem, setSelectedItem] = React.useState<LibraryItem | null>(null);
  const filters: LibraryFilters = { type: typeFilter, search: search || undefined, sort_by: sortBy, sort_order: sortOrder };
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["library", filters], queryFn: () => getLibrary(filters) });
  const items = data?.items || [];
  return (
    <div className="flex h-full min-h-0">
      <div className="flex w-64 shrink-0 flex-col border-r border-line-1" style={{ background: "var(--panel)" }}>
        <div className="border-b border-line-1 px-4 py-3"><h2 className="text-sm font-semibold text-foreground">Library</h2></div>
        <div className="flex-1 overflow-y-auto p-3">
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Type</label>
          <div className="space-y-1">
            {TYPE_FILTERS.map((f) => (<button key={f.id} onClick={() => setTypeFilter(f.id)} className={cn("flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors", typeFilter === f.id ? "bg-[var(--accent)]/10 text-foreground" : "text-foreground-secondary hover:bg-[var(--panel-hover)]")}>{f.label}</button>))}
          </div>
        </div>
      </div>
      <div className="flex flex-1 flex-col min-w-0">
        <div className="flex items-center gap-3 border-b border-line-1 px-4 py-3" style={{ background: "var(--panel)" }}>
          <div className="relative flex-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search library..." className="pl-10" /></div>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as LibraryFilters["sort_by"])} className="rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 text-sm text-foreground"><option value="created_at">Date</option><option value="title">Title</option><option value="type">Type</option></select>
          <Button size="sm" variant="outline" onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}>{sortOrder === "asc" ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}</Button>
          <div className="flex rounded-md border border-line-1">
            <button onClick={() => setViewMode("grid")} className={cn("p-2", viewMode === "grid" ? "bg-[var(--accent)]/10 text-foreground" : "text-muted-foreground")}><LayoutGrid className="h-4 w-4" /></button>
            <button onClick={() => setViewMode("list")} className={cn("p-2", viewMode === "list" ? "bg-[var(--accent)]/10 text-foreground" : "text-muted-foreground")}><List className="h-4 w-4" /></button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading && <div className="flex h-full items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}
          {error && <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground"><AlertCircle className="h-8 w-8 text-[var(--red)]" /><p className="text-sm">Failed to load library</p><Button size="sm" variant="outline" onClick={() => refetch()}>Retry</Button></div>}
          {!isLoading && !error && items.length === 0 && <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground"><BookOpen className="h-12 w-12" /><p className="text-sm">No items found</p></div>}
          {!isLoading && !error && items.length > 0 && (<>
            <p className="mb-3 text-xs text-muted-foreground">{items.length} items</p>
            {viewMode === "grid" ? (<div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">{items.map((item) => (<LibraryCard key={item.id} item={item} onClick={() => setSelectedItem(item)} />))}</div>) : (<div className="space-y-2">{items.map((item) => (<LibraryRow key={item.id} item={item} onClick={() => setSelectedItem(item)} />))}</div>)}
          </>)}
        </div>
      </div>
      {selectedItem && <LibraryPreview item={selectedItem} onClose={() => setSelectedItem(null)} />}
    </div>
  );
}

function LibraryCard({ item, onClick }: { item: LibraryItem; onClick: () => void }) {
  const config = TYPE_CONFIG[item.type];
  return (
    <button onClick={onClick} className="flex flex-col rounded-lg border border-line-1 p-3 text-left transition-colors hover:bg-[var(--panel-hover)]">
      <div className={cn("mb-2", config.color)}>{config.icon}</div>
      <h3 className="truncate text-sm font-medium text-foreground">{item.title}</h3>
      <p className="mt-1 truncate text-xs text-muted-foreground">{item.type} · {new Date(item.created_at).toLocaleDateString()}</p>
    </button>
  );
}

function LibraryRow({ item, onClick }: { item: LibraryItem; onClick: () => void }) {
  const config = TYPE_CONFIG[item.type];
  return (
    <button onClick={onClick} className="flex w-full items-center gap-3 rounded-lg border border-line-1 p-3 text-left transition-colors hover:bg-[var(--panel-hover)]">
      <div className={cn(config.color)}>{config.icon}</div>
      <div className="flex-1 min-w-0">
        <h3 className="truncate text-sm font-medium text-foreground">{item.title}</h3>
        <p className="truncate text-xs text-muted-foreground">{item.description || item.content}</p>
      </div>
      <div className="text-xs text-muted-foreground">{new Date(item.created_at).toLocaleDateString()}</div>
    </button>
  );
}

function LibraryPreview({ item, onClose }: { item: LibraryItem; onClose: () => void }) {
  const config = TYPE_CONFIG[item.type];
  return (
    <div className="flex w-80 shrink-0 flex-col border-l border-line-1" style={{ background: "var(--panel)" }}>
      <div className="flex items-center justify-between border-b border-line-1 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className={cn(config.color)}>{config.icon}</div>
          <h3 className="truncate text-sm font-semibold text-foreground">{item.title}</h3>
        </div>
        <Button size="sm" variant="ghost" onClick={onClose}>×</Button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          <div><label className="text-xs font-medium text-muted-foreground">Type</label><p className="text-sm text-foreground capitalize">{item.type}</p></div>
          {item.description && <div><label className="text-xs font-medium text-muted-foreground">Description</label><p className="text-sm text-foreground">{item.description}</p></div>}
          {item.content && <div><label className="text-xs font-medium text-muted-foreground">Content</label><p className="mt-1 max-h-40 overflow-y-auto rounded-md bg-[var(--background)] p-2 text-xs text-foreground">{item.content}</p></div>}
          <div><label className="text-xs font-medium text-muted-foreground">Created</label><p className="text-sm text-foreground">{new Date(item.created_at).toLocaleString()}</p></div>
          {item.metadata && Object.keys(item.metadata).length > 0 && <div><label className="text-xs font-medium text-muted-foreground">Metadata</label><pre className="mt-1 max-h-32 overflow-y-auto rounded-md bg-[var(--background)] p-2 text-xs text-foreground">{JSON.stringify(item.metadata, null, 2)}</pre></div>}
        </div>
      </div>
    </div>
  );
}
