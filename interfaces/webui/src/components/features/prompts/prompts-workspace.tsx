"use client";

/**
 * PromptsWorkspace — surface des prompts prédéfinis d'ETHAN Core
 * (PromptManager, core/config/prompts.py ; routes /v1/prompts).
 *
 * Les prompts sont des enregistrements métier : ils vivent dans le Core et
 * restent utilisables par le chat, la CLI, le Cookbook et les autres
 * interfaces. La recherche ci-dessous filtre la liste déjà chargée
 * (présentation seule — le Core n'expose pas d'endpoint de recherche).
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  listPrompts,
  createPrompt,
  updatePrompt,
  deletePrompt,
  type Prompt,
} from "@/lib/api/prompts";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog } from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { AlertCircle, Loader2, Plus, ScrollText, Search, Trash2 } from "lucide-react";

interface FormState {
  name: string;
  description: string;
  text: string;
  tags: string;
}

const EMPTY_FORM: FormState = { name: "", description: "", text: "", tags: "" };

export function PromptsWorkspace() {
  const addToast = useUIStore((s) => s.addToast);
  const [search, setSearch] = React.useState("");
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Prompt | null>(null);
  const [form, setForm] = React.useState<FormState>(EMPTY_FORM);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [confirmPrompt, setConfirmPrompt] = React.useState<Prompt | null>(null);

  const {
    data: prompts = [],
    isLoading,
    error,
    refetch,
  } = useQuery({ queryKey: ["prompts"], queryFn: () => listPrompts(), retry: false });

  const filtered = prompts.filter((p) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      p.name.toLowerCase().includes(q) ||
      (p.description || "").toLowerCase().includes(q) ||
      (p.tags || []).some((t) => t.toLowerCase().includes(q))
    );
  });

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setDialogOpen(true);
  };

  const openEdit = (prompt: Prompt) => {
    setEditing(prompt);
    setForm({
      name: prompt.name,
      description: prompt.description || "",
      text: prompt.text,
      tags: (prompt.tags || []).join(", "),
    });
    setFormError(null);
    setDialogOpen(true);
  };

  const handleSave = async () => {
    const tags = form.tags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    setSaving(true);
    setFormError(null);
    try {
      if (editing) {
        await updatePrompt(editing.id, {
          name: form.name,
          description: form.description,
          text: form.text,
          tags,
        });
        addToast({ type: "success", message: `Prompt « ${form.name} » mis à jour` });
      } else {
        await createPrompt({
          name: form.name,
          description: form.description,
          text: form.text,
          tags,
        });
        addToast({ type: "success", message: `Prompt « ${form.name} » créé` });
      }
      setDialogOpen(false);
      setForm(EMPTY_FORM);
      await refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Enregistrement refusé par le Core");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmPrompt) return;
    try {
      await deletePrompt(confirmPrompt.id);
      addToast({ type: "success", message: `Prompt « ${confirmPrompt.name} » supprimé` });
      await refetch();
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Suppression refusée",
      });
    } finally {
      setConfirmPrompt(null);
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div
        className="flex items-center justify-between gap-3 border-b border-line-1 px-4 py-3"
        style={{ background: "var(--panel)" }}
      >
        <div className="flex items-center gap-2">
          <ScrollText className="h-4 w-4 text-muted-foreground" />
          <div>
            <h1 className="text-sm font-semibold text-foreground">Prompts</h1>
            <p className="text-xs text-muted-foreground">
              Prompts prédéfinis stockés par ETHAN Core — réutilisables par le chat et le Cookbook.
            </p>
          </div>
        </div>
        <Button size="sm" onClick={openCreate}>
          <Plus className="h-4 w-4" /> Nouveau prompt
        </Button>
      </div>

      <div className="flex items-center gap-3 border-b border-line-1 px-4 py-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filtrer les prompts…"
            className="pl-10"
          />
        </div>
        <span className="text-xs text-muted-foreground">
          {filtered.length} {filtered.length > 1 ? "prompts" : "prompt"}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Chargement des prompts…
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-soft bg-red-soft p-4 text-sm text-red">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Impossible de charger les prompts
            </div>
            <p className="mt-1 text-xs">
              {error instanceof Error ? error.message : "Core indisponible"}
            </p>
            <Button size="sm" variant="outline" className="mt-3" onClick={() => refetch()}>
              Réessayer
            </Button>
          </div>
        )}

        {!isLoading && !error && filtered.length === 0 && (
          <div className="rounded-lg border border-line-1 p-6 text-center">
            <p className="text-sm font-medium text-foreground">Aucun prompt</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Les prompts créés ici sont persistés par ETHAN Core (PromptManager) et exposés via
              /v1/prompts à toutes les interfaces.
            </p>
          </div>
        )}

        <div className="space-y-2">
          {filtered.map((prompt) => (
            <div key={prompt.id} className="rounded-lg border border-line-1 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="truncate text-sm font-medium text-foreground">{prompt.name}</h2>
                  {prompt.description && (
                    <p className="mt-1 text-xs text-muted-foreground">{prompt.description}</p>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <Button size="sm" variant="ghost" onClick={() => openEdit(prompt)}>
                    Modifier
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setConfirmPrompt(prompt)}>
                    <Trash2 className="h-4 w-4" /> Supprimer
                  </Button>
                </div>
              </div>
              <pre className="mt-2 max-h-24 overflow-y-auto whitespace-pre-wrap rounded-md bg-[var(--background)] p-2 text-xs text-foreground-secondary">
                {prompt.text}
              </pre>
              {(prompt.tags || []).length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {(prompt.tags || []).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md bg-[var(--panel-hover)] px-2 py-0.5 text-xs text-muted-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? "Modifier le prompt" : "Nouveau prompt"}
        size="md"
      >
        <div className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Nom</label>
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="ex: revue de code"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Description</label>
            <Input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Texte du prompt</label>
            <Textarea
              value={form.text}
              onChange={(e) => setForm({ ...form, text: e.target.value })}
              rows={6}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Tags (séparés par des virgules)</label>
            <Input
              value={form.tags}
              onChange={(e) => setForm({ ...form, tags: e.target.value })}
              placeholder="code, revue"
            />
          </div>
          {formError && <p className="text-sm text-red">{formError}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setDialogOpen(false)}>
              Annuler
            </Button>
            <Button onClick={handleSave} disabled={saving || !form.name.trim() || !form.text.trim()}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {editing ? "Enregistrer" : "Créer"}
            </Button>
          </div>
        </div>
      </Dialog>

      <ConfirmDialog
        open={confirmPrompt !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmPrompt(null);
        }}
        title="Supprimer ce prompt ?"
        message={confirmPrompt ? `« ${confirmPrompt.name} » sera supprimé du Core.` : undefined}
        confirmLabel="Supprimer"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  );
}
