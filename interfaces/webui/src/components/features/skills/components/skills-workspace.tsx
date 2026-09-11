"use client";

/**
 * SkillsWorkspace — Gestion complète des skills ETHAN (Core-owned).
 *
 * UX inspirée d'Open-WebUI : navigation par dossiers côté gauche, grille de
 * skills filtrable, actions courtes en dialogues. Les skills sont gérées par
 * ETHAN Core (SkillStore) ; le WebUI ne présente et ne configure que.
 *
 * Couvre : liste, recherche, filtres (type/état/dossier), création édition
 * (modèle unifié prompt|pipeline), activation/désactivation, suppression,
 * détail, classement dans les dossiers utilisateur, import/export, exécution.
 */

import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useSkills } from "@/components/features/skills/hooks/use-skills";
import {
  SkillDialog,
  ExecuteSkillDialog,
} from "@/components/features/skills/components/skill-dialog";
import {
  listFolderTree,
  getFolderIndex,
  moveResource as apiMoveResource,
  type FolderTree as FolderTreeNode,
} from "@/lib/api/folders";
import { PageHeader } from "@/components/shared/page-header";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import {
  Search,
  Loader2,
  Plus,
  Trash2,
  Pencil,
  Power,
  Play,
  Code2,
  Upload,
  Download,
  Eye,
  Folder,
  FolderOpen,
  FolderTree,
  ChevronRight,
  Boxes,
  Layers,
} from "lucide-react";
import type { Skill } from "@/lib/api/skills";
import { cn } from "@/lib/utils";

export function SkillsWorkspace() {
  const {
    skills,
    isLoading,
    error,
    createSkill,
    updateSkill,
    deleteSkill,
    toggleSkill,
    runSkill,
    importSkills,
    exportSkills,
    isCreating,
    isRunning,
    isImporting,
  } = useSkills();
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  // ── Filtres ─────────────────────────────────────────────────────────
  const [search, setSearch] = React.useState("");
  const [kindFilter, setKindFilter] = React.useState<"all" | "prompt" | "pipeline">("all");
  const [activeFilter, setActiveFilter] = React.useState<"all" | "active" | "inactive">("all");
  /** "all" | "untagged" | <folderId> */
  const [folderFilter, setFolderFilter] = React.useState<string>("all");

  // ── Dossiers (organisation Core, aucun dossier imposé) ──────────────
  const { data: folderTree = [] } = useQuery<FolderTreeNode[]>({
    queryKey: ["folders-tree"],
    queryFn: () => listFolderTree(),
    staleTime: 30_000,
  });
  const { data: skillIndex = {} } = useQuery<Record<string, string[]>>({
    queryKey: ["folders-index", "skill"],
    queryFn: () => getFolderIndex("skill"),
    staleTime: 30_000,
  });

  const skillFolderIds = (skillId: string): string[] =>
    Object.entries(skillIndex)
      .filter(([, ids]) => ids.includes(skillId))
      .map(([folderId]) => folderId);

  // ── Formulaire d'édition ────────────────────────────────────────────
  const [editorOpen, setEditorOpen] = React.useState(false);
  const [editingSkill, setEditingSkill] = React.useState<Skill | null>(null);
  const [formName, setFormName] = React.useState("");
  const [formDescription, setFormDescription] = React.useState("");
  const [formContent, setFormContent] = React.useState("");
  const [formTags, setFormTags] = React.useState("");
  const [formKind, setFormKind] = React.useState<"prompt" | "pipeline">("prompt");
  const [formRequiredTools, setFormRequiredTools] = React.useState("");
  const [formValves, setFormValves] = React.useState("");

  // ── Détail / classement / exécution / suppression ───────────────────
  const [detailSkill, setDetailSkill] = React.useState<Skill | null>(null);
  const [classifySkill, setClassifySkill] = React.useState<Skill | null>(null);
  const [classifySelection, setClassifySelection] = React.useState<string[]>([]);
  const [isClassifying, setIsClassifying] = React.useState(false);
  const [execOpen, setExecOpen] = React.useState(false);
  const [execSkill, setExecSkill] = React.useState<Skill | null>(null);
  const [execInput, setExecInput] = React.useState("");
  const [execResult, setExecResult] = React.useState<string>("");
  const [execError, setExecError] = React.useState<string | null>(null);
  const [pendingDeleteSkill, setPendingDeleteSkill] = React.useState<Skill | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const filtered = skills.filter((s) => {
    const q = search.toLowerCase();
    if (!s.name.toLowerCase().includes(q) && !(s.description || "").toLowerCase().includes(q))
      return false;
    if (kindFilter !== "all" && s.kind !== kindFilter) return false;
    if (activeFilter === "active" && !s.is_active) return false;
    if (activeFilter === "inactive" && s.is_active) return false;
    if (folderFilter === "untagged") {
      if (skillFolderIds(s.id).length > 0) return false;
    } else if (folderFilter !== "all") {
      if (!(skillIndex[folderFilter] ?? []).includes(s.id)) return false;
    }
    return true;
  });

  /** Nombre de skills d'un dossier (index Core). */
  const folderSkillCount = (folderId: string): number =>
    (skillIndex[folderId] ?? []).length;
  const untaggedCount = skills.filter((s) => skillFolderIds(s.id).length === 0).length;

  const openCreate = () => {
    setEditingSkill(null);
    setFormName("");
    setFormDescription("");
    setFormContent("");
    setFormTags("");
    setFormKind("prompt");
    setFormRequiredTools("");
    setFormValves("");
    setEditorOpen(true);
  };

  const openEdit = (skill: Skill) => {
    setEditingSkill(skill);
    setFormName(skill.name);
    setFormDescription(skill.description || "");
    setFormContent(skill.content || "");
    setFormTags((skill.tags || []).join(", "));
    setFormKind(skill.kind === "pipeline" ? "pipeline" : "prompt");
    setFormRequiredTools((skill.required_tools || []).join(", "));
    setFormValves(
      skill.valves && Object.keys(skill.valves).length > 0
        ? JSON.stringify(skill.valves, null, 2)
        : "",
    );
    setEditorOpen(true);
  };

  const handleSave = async () => {
    const tags = formTags.split(",").map((t) => t.trim()).filter(Boolean);
    let valves: Record<string, unknown> | undefined;
    if (formValves.trim()) {
      try {
        valves = JSON.parse(formValves);
        if (typeof valves !== "object" || valves === null) throw new Error("objet attendu");
      } catch {
        addToast({ type: "error", message: "Valves invalides : JSON objet attendu." });
        return;
      }
    }
    const requiredTools = formKind === "pipeline"
      ? formRequiredTools.split(",").map((t) => t.trim()).filter(Boolean)
      : undefined;

    if (editingSkill) {
      const r = await updateSkill(editingSkill.id, {
        name: formName,
        description: formDescription,
        ...(formKind === "prompt" ? { content: formContent } : {}),
        tags,
        ...(valves !== undefined ? { valves } : {}),
        ...(formKind === "pipeline" && requiredTools
          ? { required_tools: requiredTools }
          : {}),
      });
      if (r.error) {
        addToast({ type: "error", message: r.error });
        return;
      }
    } else {
      const r = await createSkill({
        name: formName,
        description: formDescription,
        kind: formKind,
        ...(formKind === "prompt" ? { content: formContent } : {}),
        tags,
        ...(formKind === "pipeline" && requiredTools
          ? { required_tools: requiredTools }
          : {}),
        ...(valves !== undefined ? { valves } : {}),
      });
      if (r.error) {
        addToast({ type: "error", message: r.error });
        return;
      }
    }
    setEditorOpen(false);
  };

  const handleToggle = async (skill: Skill) => {
    const r = await toggleSkill(skill.id);
    if (r.error) addToast({ type: "error", message: r.error });
  };

  const confirmDeleteSkill = async () => {
    if (!pendingDeleteSkill) return;
    const r = await deleteSkill(pendingDeleteSkill.id);
    setPendingDeleteSkill(null);
    if (r.error) addToast({ type: "error", message: r.error });
  };

  const handleExecute = async () => {
    if (!execSkill || !execInput.trim()) return;
    setExecError(null);
    setExecResult("");
    const r = await runSkill(execSkill.id, execInput);
    if (r.error) {
      setExecError(r.error);
      return;
    }
    setExecResult(r.data?.output ?? "(aucune sortie)");
  };

  const openClassify = (skill: Skill) => {
    setClassifySkill(skill);
    setClassifySelection(skillFolderIds(skill.id));
  };

  const saveClassification = async () => {
    if (!classifySkill) return;
    setIsClassifying(true);
    try {
      await apiMoveResource("skill", classifySkill.id, classifySelection);
      queryClient.invalidateQueries({ queryKey: ["folders-tree"] });
      queryClient.invalidateQueries({ queryKey: ["folders-index"] });
      addToast({ type: "success", message: "Classement mis à jour" });
      setClassifySkill(null);
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Échec du classement",
      });
    } finally {
      setIsClassifying(false);
    }
  };

  const handleExport = async () => {
    const r = await exportSkills();
    if (r.error || !r.data) {
      addToast({ type: "error", message: r.error || "Échec de l'export" });
      return;
    }
    const blob = new Blob([JSON.stringify({ skills: r.data }, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ethan-skills-export.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text());
      const records = Array.isArray(parsed) ? parsed : (parsed.skills ?? []);
      await importSkills(records);
    } catch {
      addToast({ type: "error", message: "Fichier JSON invalide" });
    }
  };

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Skills"
        description="Compétences ETHAN — instructions et pipelines d'outils gérés par le Core."
        icon={<Code2 className="h-5 w-5" />}
        count={filtered.length}
        actions={
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept="application/json"
              className="hidden"
              onChange={handleImportFile}
            />
            <Button variant="ghost" size="sm" onClick={() => fileInputRef.current?.click()} disabled={isImporting}>
              <Upload className="h-4 w-4" />
              Importer
            </Button>
            <Button variant="ghost" size="sm" onClick={handleExport}>
              <Download className="h-4 w-4" />
              Exporter
            </Button>
            <Button variant="default" size="sm" onClick={openCreate} disabled={isCreating}>
              <Plus className="h-4 w-4" />
              Nouveau skill
            </Button>
          </div>
        }
      />

      <div className="flex min-h-0 flex-1">
        {/* ── Sidebar : navigation par dossiers (organisation utilisateur) ── */}
        <aside className="flex w-56 shrink-0 flex-col border-r border-line-1 px-3 py-3">
          <p className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-foreground-tertiary">
            Dossiers
          </p>
          <button
            onClick={() => setFolderFilter("all")}
            className={cn(
              "mb-0.5 flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm",
              folderFilter === "all" ? "bg-accent/10 text-foreground" : "text-foreground-secondary hover:bg-bg-2",
            )}
          >
            <FolderTree className="h-4 w-4" />
            <span className="flex-1 text-left">Tous</span>
            <Badge variant="dim" size="sm">{skills.length}</Badge>
          </button>
          <button
            onClick={() => setFolderFilter("untagged")}
            className={cn(
              "mb-0.5 flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm",
              folderFilter === "untagged" ? "bg-accent/10 text-foreground" : "text-foreground-secondary hover:bg-bg-2",
            )}
          >
            <Boxes className="h-4 w-4" />
            <span className="flex-1 text-left">Non classés</span>
            <Badge variant="dim" size="sm">{untaggedCount}</Badge>
          </button>
          <FolderNav
            nodes={folderTree}
            depth={0}
            activeId={folderFilter}
            countFn={folderSkillCount}
            onSelect={setFolderFilter}
          />
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <div className="flex flex-wrap items-center gap-3 border-b border-line-1 px-4 py-2">
            <div className="relative flex-1 max-w-md">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Rechercher un skill…"
                className="w-full rounded-lg border border-line-1 bg-bg-1 py-1.5 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
              />
            </div>
            <select
              value={kindFilter}
              onChange={(e) => setKindFilter(e.target.value as typeof kindFilter)}
              className="h-9 rounded-lg border border-line-2 bg-background px-2 text-sm text-foreground"
              aria-label="Filtrer par type"
            >
              <option value="all">Tous les types</option>
              <option value="prompt">Prompt</option>
              <option value="pipeline">Pipeline</option>
            </select>
            <select
              value={activeFilter}
              onChange={(e) => setActiveFilter(e.target.value as typeof activeFilter)}
              className="h-9 rounded-lg border border-line-2 bg-background px-2 text-sm text-foreground"
              aria-label="Filtrer par état"
            >
              <option value="all">Tous les états</option>
              <option value="active">Actifs</option>
              <option value="inactive">Désactivés</option>
            </select>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
            {isLoading ? (
              <div className="flex items-center justify-center py-12 text-foreground-tertiary">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : error ? (
              <p className="text-sm text-red">{error}</p>
            ) : filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10">
                  <Layers className="h-6 w-6 text-accent" />
                </div>
                <h2 className="text-lg font-semibold text-foreground">
                  {search || kindFilter !== "all" || activeFilter !== "all" || folderFilter !== "all"
                    ? "Aucun skill ne correspond aux filtres"
                    : "Aucun skill"}
                </h2>
                <p className="mt-2 max-w-sm text-sm text-foreground-tertiary">
                  {search || kindFilter !== "all" || activeFilter !== "all" || folderFilter !== "all"
                    ? "Modifiez vos critères de recherche ou de dossier."
                    : "Créez votre premier skill avec « Nouveau skill »."}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {filtered.map((skill) => (
                  <SkillCard
                    key={skill.id}
                    skill={skill}
                    onToggle={handleToggle}
                    onEdit={openEdit}
                    onDelete={(s) => setPendingDeleteSkill(s)}
                    onDetail={setDetailSkill}
                    onRun={(s) => {
                      setExecSkill(s);
                      setExecInput("");
                      setExecResult("");
                      setExecError(null);
                      setExecOpen(true);
                    }}
                    onClassify={openClassify}
                  />
                ))}
              </div>
            )}
          </div>
        </section>
      </div>

      <SkillDialog
        open={editorOpen}
        editingSkill={editingSkill}
        isCreating={isCreating}
        formName={formName}
        formDescription={formDescription}
        formContent={formContent}
        formTags={formTags}
        formKind={formKind}
        formRequiredTools={formRequiredTools}
        formValves={formValves}
        setFormName={setFormName}
        setFormDescription={setFormDescription}
        setFormContent={setFormContent}
        setFormTags={setFormTags}
        setFormKind={setFormKind}
        setFormRequiredTools={setFormRequiredTools}
        setFormValves={setFormValves}
        onClose={() => setEditorOpen(false)}
        onSave={handleSave}
      />

      <SkillClassifyDialog
        skill={classifySkill}
        open={classifySkill !== null}
        selection={classifySelection}
        tree={folderTree}
        onChange={setClassifySelection}
        isSaving={isClassifying}
        onClose={() => setClassifySkill(null)}
        onSave={saveClassification}
      />

      <SkillDetailDialog skill={detailSkill} onClose={() => setDetailSkill(null)} />

      <ExecuteSkillDialog
        open={execOpen}
        skill={execSkill}
        isExecuting={isRunning}
        input={execInput}
        setInput={setExecInput}
        error={execError}
        result={execResult}
        onClose={() => setExecOpen(false)}
        onExecute={handleExecute}
      />

      <ConfirmDialog
        open={pendingDeleteSkill !== null}
        onOpenChange={(o) => { if (!o) setPendingDeleteSkill(null); }}
        title="Supprimer le skill"
        message={pendingDeleteSkill ? `Supprimer le skill « ${pendingDeleteSkill.name} » ? Cette action est irréversible.` : ""}
        confirmLabel="Supprimer"
        destructive
        onConfirm={confirmDeleteSkill}
      />
    </div>
  );
}

function FolderNav({
  nodes,
  depth,
  activeId,
  countFn,
  onSelect,
}: {
  nodes: FolderTreeNode[];
  depth: number;
  activeId: string;
  countFn: (folderId: string) => number;
  onSelect: (folderId: string) => void;
}) {
  if (nodes.length === 0) return null;
  return (
    <>
      {nodes.map((node) => {
        const isActive = activeId === node.id;
        const hasChildren = node.children.length > 0;
        return (
          <div key={node.id}>
            <button
              onClick={() => onSelect(node.id)}
              style={{ paddingLeft: `${8 + depth * 14}px` }}
              className={cn(
                "mb-0.5 flex w-full items-center gap-2 rounded-lg py-1.5 pr-2 text-sm",
                isActive
                  ? "bg-accent/10 text-foreground"
                  : "text-foreground-secondary hover:bg-bg-2",
              )}
            >
              {hasChildren ? (
                <ChevronRight className="h-3.5 w-3.5 text-foreground-tertiary" />
              ) : (
                <span className="w-3.5" />
              )}
              {isActive ? (
                <FolderOpen className="h-4 w-4 text-accent" />
              ) : (
                <Folder className="h-4 w-4 text-foreground-tertiary" />
              )}
              <span className="flex-1 truncate text-left">{node.name}</span>
              <Badge variant="dim" size="sm">{countFn(node.id)}</Badge>
            </button>
            {hasChildren && (
              <FolderNav
                nodes={node.children}
                depth={depth + 1}
                activeId={activeId}
                countFn={countFn}
                onSelect={onSelect}
              />
            )}
          </div>
        );
      })}
    </>
  );
}

function SkillCard({
  skill,
  onToggle,
  onEdit,
  onDelete,
  onDetail,
  onRun,
  onClassify,
}: {
  skill: Skill;
  onToggle: (s: Skill) => void;
  onEdit: (s: Skill) => void;
  onDelete: (s: Skill) => void;
  onDetail: (s: Skill) => void;
  onRun: (s: Skill) => void;
  onClassify: (s: Skill) => void;
}) {
  const hasExecutableContent = !!(skill.content && skill.content.trim());
  const successRate =
    skill.total_executions > 0
      ? Math.round(((skill.success_count ?? 0) / skill.total_executions) * 100)
      : null;

  return (
    <div
      className="group relative flex cursor-pointer flex-col rounded-xl border border-line-1 bg-bg-1 p-4 transition-all hover:border-accent/50 hover:shadow-sm"
      onClick={() => onDetail(skill)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onDetail(skill);
        }
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/10">
            <Code2 className="h-4 w-4 text-accent" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-foreground">{skill.name}</p>
            <p className="truncate text-xs text-foreground-tertiary">
              {skill.description || "—"}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Badge variant={skill.kind === "pipeline" ? "accent" : "info"} size="sm">
            {skill.kind === "pipeline" ? "Pipeline" : "Prompt"}
          </Badge>
          {skill.is_builtin && <Badge variant="secondary" size="sm">Built-in</Badge>}
          <Badge variant={skill.is_active ? "success" : "dim"} size="sm">
            {skill.is_active ? "Actif" : "Désactivé"}
          </Badge>
        </div>
      </div>

      <div className="mt-3 flex flex-col gap-1.5">
        {skill.required_tools && skill.required_tools.length > 0 && (
          <p className="truncate text-[11px] text-foreground-tertiary">
            Outils requis : <span className="text-foreground-secondary">{skill.required_tools.join(", ")}</span>
          </p>
        )}
        {skill.total_executions > 0 && (
          <p className="text-[11px] text-foreground-tertiary">
            {skill.total_executions} exécution{skill.total_executions > 1 ? "s" : ""}
            {successRate !== null && ` · ${successRate}% succès`}
          </p>
        )}
        {(skill.tags || []).length > 0 && (
          <div className="flex flex-wrap gap-1">
            {skill.tags.slice(0, 4).map((t) => (
              <Badge key={t} variant="secondary" size="sm">{t}</Badge>
            ))}
            {skill.tags.length > 4 && <Badge variant="dim" size="sm">+{skill.tags.length - 4}</Badge>}
          </div>
        )}
      </div>

      <div className="mt-auto flex items-center justify-between border-t border-line-1 pt-3">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={(e) => {
              e.stopPropagation();
              onToggle(skill);
            }}
            title={skill.is_active ? "Désactiver" : "Activer"}
          >
            <Power className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={(e) => {
              e.stopPropagation();
              onEdit(skill);
            }}
            title="Modifier"
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={(e) => {
              e.stopPropagation();
              onClassify(skill);
            }}
            title="Organiser dans les dossiers"
          >
            <Folder className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 text-red/80 hover:bg-red-soft hover:text-red"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(skill);
            }}
            title="Supprimer"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={(e) => {
              e.stopPropagation();
              onDetail(skill);
            }}
            title="Voir le détail"
          >
            <Eye className="h-3.5 w-3.5" />
          </Button>
          {hasExecutableContent && (
            <Button
              variant="secondary"
              size="sm"
              className="h-7"
              onClick={(e) => {
                e.stopPropagation();
                onRun(skill);
              }}
              disabled={!skill.is_active}
              title={skill.is_active ? "Exécuter la skill" : "Activer la skill pour l'exécuter"}
            >
              <Play className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function SkillClassifyDialog({
  skill,
  open,
  selection,
  tree,
  onChange,
  isSaving,
  onClose,
  onSave,
}: {
  skill: Skill | null;
  open: boolean;
  selection: string[];
  tree: FolderTreeNode[];
  onChange: (v: string[]) => void;
  isSaving: boolean;
  onClose: () => void;
  onSave: () => void;
}) {
  const toggle = (folderId: string) => {
    if (selection.includes(folderId)) {
      onChange(selection.filter((id) => id !== folderId));
    } else {
      onChange([...selection, folderId]);
    }
  };

  const renderTree = (nodes: FolderTreeNode[], depth: number) =>
    nodes.map((node) => (
      <div key={node.id} style={{ paddingLeft: `${depth * 16}px` }}>
        <label className="flex cursor-pointer items-center gap-1.5 py-1">
          <input
            type="checkbox"
            checked={selection.includes(node.id)}
            onChange={() => toggle(node.id)}
            className="h-3.5 w-3.5"
          />
          <Folder className="h-4 w-4 text-foreground-tertiary" />
          <span className="text-sm text-foreground">{node.name}</span>
        </label>
        {node.children.length > 0 && renderTree(node.children, depth + 1)}
      </div>
    ));

  return (
    <Dialog open={open} onClose={onClose} title={`Organiser — ${skill?.name ?? ""}`} size="md">
      <div className="flex flex-col gap-4">
        <p className="text-sm text-foreground-tertiary">
          Classez ce skill dans un ou plusieurs dossiers. Une même skill peut apparaître dans
          plusieurs dossiers ; aucun dossier n&apos;est imposé (laisser vide = « non classé »).
        </p>
        {tree.length === 0 ? (
          <p className="rounded-lg border border-line-1 bg-bg-1 px-3 py-3 text-sm text-foreground-tertiary">
            Aucun dossier pour le moment. Créez vos dossiers depuis l&apos;espace <strong>Dossiers</strong>.
          </p>
        ) : (
          <div className="max-h-64 overflow-y-auto rounded-lg border border-line-1 bg-bg-1 px-2 py-2">
            {renderTree(tree, 0)}
          </div>
        )}
        <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
          <Button variant="secondary" onClick={onClose}>Annuler</Button>
          <Button onClick={onSave} disabled={isSaving}>
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Enregistrer
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

function SkillDetailDialog({
  skill,
  onClose,
}: {
  skill: Skill | null;
  onClose: () => void;
}) {
  if (!skill) return null;
  const successRate =
    skill.total_executions > 0
      ? Math.round(((skill.success_count ?? 0) / skill.total_executions) * 100)
      : null;
  const hasValves = skill.valves && Object.keys(skill.valves).length > 0;

  return (
    <Dialog open={skill !== null} onClose={onClose} title={skill.name} size="lg">
      <div className="flex flex-col gap-4">
        {skill.description && (
          <p className="text-sm text-foreground-secondary">{skill.description}</p>
        )}

        <div className="grid grid-cols-2 gap-x-5 gap-y-1.5 text-xs sm:grid-cols-4">
          <div>
            <p className="text-foreground-tertiary">Type</p>
            <p className="text-foreground">{skill.kind === "pipeline" ? "Pipeline" : "Prompt"}</p>
          </div>
          <div>
            <p className="text-foreground-tertiary">Version</p>
            <p className="text-foreground">{skill.version || "—"}</p>
          </div>
          <div>
            <p className="text-foreground-tertiary">Auteur</p>
            <p className="text-foreground">{skill.author || "—"}</p>
          </div>
          <div>
            <p className="text-foreground-tertiary">Source</p>
            <p className="text-foreground">{skill.is_builtin ? "Built-in" : "Utilisateur"}</p>
          </div>
          <div>
            <p className="text-foreground-tertiary">État</p>
            <Badge variant={skill.is_active ? "success" : "dim"} size="sm">
              {skill.is_active ? "Actif" : "Désactivé"}
            </Badge>
          </div>
          <div>
            <p className="text-foreground-tertiary">Exécutions</p>
            <p className="text-foreground">
              {skill.total_executions}
              {successRate !== null && ` (${successRate}% succès)`}
            </p>
          </div>
          <div>
            <p className="text-foreground-tertiary">Créé</p>
            <p className="text-foreground">
              {skill.created_at ? new Date(skill.created_at).toLocaleDateString() : "—"}
            </p>
          </div>
          <div>
            <p className="text-foreground-tertiary">Mis à jour</p>
            <p className="text-foreground">
              {skill.updated_at ? new Date(skill.updated_at).toLocaleDateString() : "—"}
            </p>
          </div>
        </div>

        {skill.required_tools && skill.required_tools.length > 0 && (
          <div>
            <p className="mb-1 text-xs font-medium text-foreground-tertiary">Outils requis</p>
            <div className="flex flex-wrap gap-1">
              {skill.required_tools.map((t) => (
                <Badge key={t} variant="accent" size="sm">{t}</Badge>
              ))}
            </div>
          </div>
        )}

        {skill.kind === "prompt" && skill.content && (
          <div>
            <p className="mb-1 text-xs font-medium text-foreground-tertiary">Contenu / instructions</p>
            <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg border border-line-1 bg-bg-1 p-3 font-mono text-xs text-foreground-secondary">
              {skill.content}
            </pre>
          </div>
        )}

        {skill.kind === "pipeline" && skill.steps && skill.steps.length > 0 && (
          <div>
            <p className="mb-1 text-xs font-medium text-foreground-tertiary">Étapes du pipeline</p>
            <div className="max-h-64 overflow-y-auto rounded-lg border border-line-1 bg-bg-1">
              {skill.steps.map((step, i) => (
                <div key={`${step.id ?? i}`} className="flex items-center gap-2 border-b border-line-1 px-3 py-2 text-sm last:border-0">
                  <Badge variant="dim" size="sm">{i + 1}</Badge>
                  <span className="min-w-0 flex-1 truncate text-foreground">
                    {String(step.name ?? step.id ?? `Étape ${i + 1}`)}
                  </span>
                  {step.tool_id ? (
                    <Badge variant="secondary" size="sm">{String(step.tool_id)}</Badge>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        )}

        {hasValves && (
          <div>
            <p className="mb-1 text-xs font-medium text-foreground-tertiary">Valves (configuration)</p>
            <pre className="max-h-32 overflow-y-auto rounded-lg border border-line-1 bg-bg-1 p-2 font-mono text-xs text-foreground-secondary">
              {JSON.stringify(skill.valves, null, 2)}
            </pre>
          </div>
        )}

        {skill.tags && skill.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {skill.tags.map((t) => (
              <Badge key={t} variant="secondary" size="sm">{t}</Badge>
            ))}
          </div>
        )}

        <div className="flex justify-end border-t border-line-1 pt-3">
          <Button variant="secondary" onClick={onClose}>Fermer</Button>
        </div>
      </div>
    </Dialog>
  );
}