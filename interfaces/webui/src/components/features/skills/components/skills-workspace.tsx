"use client";

/**
 * SkillsWorkspace — Gestion des skills Core (SkillStore).
 *
 * Fonctionnalités : list, create, edit, toggle enable/disable, delete et
 * exécution (SkillManager Core). Pas de mock : chaque action appelle l'API.
 */

import * as React from "react";
import { useSkills } from "@/components/features/skills/hooks/use-skills";
import { SkillDialog, ExecuteSkillDialog } from "@/components/features/skills/components/skill-dialog";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, Loader2, Plus, Trash2, Pencil, Power, Play, Code2 } from "lucide-react";
import type { Skill } from "@/lib/api/skills";

export function SkillsWorkspace() {
  const {
    skills,
    isLoading,
    error,
    createSkill,
    updateSkill,
    deleteSkill,
    toggleSkill,
    executeSkill,
    isCreating,
    isExecuting,
  } = useSkills();
  const addToast = useUIStore((s) => s.addToast);

  const [search, setSearch] = React.useState("");
  const [editorOpen, setEditorOpen] = React.useState(false);
  const [editingSkill, setEditingSkill] = React.useState<Skill | null>(null);
  const [execOpen, setExecOpen] = React.useState(false);
  const [execSkill, setExecSkill] = React.useState<Skill | null>(null);
  const [execResult, setExecResult] = React.useState<string>("");
  const [execError, setExecError] = React.useState<string | null>(null);

  const [formName, setFormName] = React.useState("");
  const [formDescription, setFormDescription] = React.useState("");
  const [formContent, setFormContent] = React.useState("");
  const [formTags, setFormTags] = React.useState("");

  const filtered = skills.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      (s.description || "").toLowerCase().includes(search.toLowerCase()),
  );

  const openCreate = () => {
    setEditingSkill(null);
    setFormName("");
    setFormDescription("");
    setFormContent("");
    setFormTags("");
    setEditorOpen(true);
  };

  const openEdit = (skill: Skill) => {
    setEditingSkill(skill);
    setFormName(skill.name);
    setFormDescription(skill.description || "");
    setFormContent(skill.content || "");
    setFormTags((skill.tags || []).join(", "));
    setEditorOpen(true);
  };

  const handleSave = async () => {
    if (!formName.trim()) return;
    const tags = formTags.split(",").map((t) => t.trim()).filter(Boolean);
    if (editingSkill) {
      const r = await updateSkill(editingSkill.id, {
        name: formName.trim(),
        description: formDescription.trim(),
        content: formContent,
        tags,
      });
      if (r.error) addToast({ type: "error", message: r.error });
    } else {
      const r = await createSkill({
        name: formName.trim(),
        description: formDescription.trim(),
        content: formContent,
        tags,
      });
      if (r.error) addToast({ type: "error", message: r.error });
    }
    setEditorOpen(false);
  };

  const handleToggle = async (skill: Skill) => {
    const r = await toggleSkill(skill.id);
    if (r.error) addToast({ type: "error", message: r.error });
  };

  const handleDelete = async (skill: Skill) => {
    if (!window.confirm(`Supprimer le skill « ${skill.name} » ?`)) return;
    const r = await deleteSkill(skill.id);
    if (r.error) addToast({ type: "error", message: r.error });
  };

  const handleExecute = async () => {
    if (!execSkill) return;
    setExecError(null);
    setExecResult("");
    const r = await executeSkill(execSkill.id, {});
    if (r.error) setExecError(r.error);
    else if (r.data) {
      if (r.data.status === "failed") setExecError(String(r.data.result) || "Échec");
      else setExecResult(String(r.data.result ?? "(pas de résultat)"));
    }
  };
  return (
    <div className="flex h-full flex-col gap-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Skills</h1>
        <Button variant="default" size="sm" onClick={openCreate} disabled={isCreating}>
          <Plus className="h-4 w-4" />
          Nouveau skill
        </Button>
      </div>

      <Input
        placeholder="Rechercher un skill…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        icon={<Search className="h-4 w-4" />}
        className="max-w-sm"
      />

      {isLoading ? (
        <div className="flex items-center justify-center py-12 text-foreground-tertiary">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
      ) : error ? (
        <p className="text-red">{error}</p>
      ) : filtered.length === 0 ? (
        <p className="py-8 text-center text-foreground-tertiary">Aucun skill trouvé.</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((skill) => (
            <div key={skill.id} className="flex flex-col gap-3 rounded-xl border border-line-2 bg-background p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <Code2 className="h-4 w-4 text-accent" />
                  <h3 className="font-semibold text-foreground">{skill.name}</h3>
                </div>
                <Badge variant={skill.is_active ? "success" : "dim"}>
                  {skill.is_active ? "Actif" : "Désactivé"}
                </Badge>
              </div>
              {skill.description && (
                <p className="line-clamp-2 text-sm text-foreground-secondary">{skill.description}</p>
              )}
              <p className="line-clamp-3 rounded-md bg-elevated p-2 font-mono text-xs text-foreground-tertiary">
                {skill.content?.slice(0, 160) || "Aucun contenu"}
              </p>
              {skill.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {skill.tags.map((t) => (
                    <Badge key={t} variant="secondary" size="sm">{t}</Badge>
                  ))}
                </div>
              )}
              <div className="mt-auto flex items-center justify-between border-t border-line-1 pt-3">
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => handleToggle(skill)} title={skill.is_active ? "Désactiver" : "Activer"}>
                    <Power className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => openEdit(skill)} title="Modifier">
                    <Pencil className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(skill)} title="Supprimer" className="text-red/80 hover:text-red">
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setExecSkill(skill);
                    setExecResult("");
                    setExecError(null);
                    setExecOpen(true);
                  }}
                  disabled={!skill.is_active}
                  title={skill.is_active ? "Exécuter" : "Activer le skill pour l'exécuter"}
                >
                  <Play className="h-3.5 w-3.5" />
                  Exécuter
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <SkillDialog
        open={editorOpen}
        editingSkill={editingSkill}
        isCreating={isCreating}
        formName={formName}
        formDescription={formDescription}
        formContent={formContent}
        formTags={formTags}
        setFormName={setFormName}
        setFormDescription={setFormDescription}
        setFormContent={setFormContent}
        setFormTags={setFormTags}
        onClose={() => setEditorOpen(false)}
        onSave={handleSave}
      />

      <ExecuteSkillDialog
        open={execOpen}
        skill={execSkill}
        isExecuting={isExecuting}
        error={execError}
        result={execResult}
        onClose={() => setExecOpen(false)}
        onExecute={handleExecute}
      />
    </div>
  );
}
