"use client";

/**
 * Page Notes — CRUD + recherche.
 * Logique métier dans ETHAN Core (NoteManager) ; cette page ne fait
 * que rendre et envoyer les actions via l'API.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listNotes, searchNotes, createNote, updateNote, deleteNote,
  type Note,
} from "@/lib/api/capabilities";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { StickyNote, Plus, Trash2, Pin, Search } from "lucide-react";

export default function NotesPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [search, setSearch] = React.useState("");
  const [editing, setEditing] = React.useState<Note | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [title, setTitle] = React.useState("");
  const [content, setContent] = React.useState("");

  const { data: notes = [], isLoading } = useQuery({
    queryKey: ["notes", search],
    queryFn: () => (search.trim() ? searchNotes(search) : listNotes()),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["notes"] });

  const createMutation = useMutation({
    mutationFn: createNote,
    onSuccess: () => { invalidate(); addToast({ type: "success", message: "Note créée" }); closeDialog(); },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string; content?: string; pinned?: boolean } }) => updateNote(id, data),
    onSuccess: () => { invalidate(); addToast({ type: "success", message: "Note mise à jour" }); closeDialog(); },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteNote,
    onSuccess: () => { invalidate(); addToast({ type: "success", message: "Note supprimée" }); },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  function closeDialog() {
    setDialogOpen(false);
    setEditing(null);
    setTitle("");
    setContent("");
  }

  function openNew() {
    setEditing(null);
    setTitle("");
    setContent("");
    setDialogOpen(true);
  }

  function openEdit(note: Note) {
    setEditing(note);
    setTitle(note.title);
    setContent(note.content);
    setDialogOpen(true);
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between gap-3 px-4 py-3" style={{ background: "var(--panel)", borderBottom: "1px solid var(--border)" }}>
        <div className="flex items-center gap-2">
          <StickyNote size={18} className="text-accent" />
          <h1 className="text-base font-semibold">Notes</h1>
        </div>
        <div className="flex flex-1 items-center justify-end gap-2">
          <div className="relative w-64">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 opacity-50" />
            <Input placeholder="Rechercher…" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
          <Button size="sm" onClick={openNew}><Plus size={14} /> Note</Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {notes.length === 0 && !isLoading && (
          <p className="py-10 text-center text-sm opacity-60">Aucune note. Créez-en une !</p>
        )}
        <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-3">
          {notes.map((note) => (
            <button
              key={note.id}
              onClick={() => openEdit(note)}
              className="group rounded-lg border p-3 text-left transition-colors hover:border-accent"
              style={{ background: "var(--panel)", borderColor: "var(--border)" }}
            >
              <div className="mb-1 flex items-start justify-between gap-2">
                <span className="flex-1 truncate text-sm font-medium">{note.title || "(sans titre)"}</span>
                <span className="flex shrink-0 items-center gap-1">
                  <button
                    onClick={(e) => { e.stopPropagation(); updateMutation.mutate({ id: note.id, data: { pinned: !note.pinned } }); }}
                    aria-label="Épingler"
                    style={{ color: note.pinned ? "var(--accent)" : undefined }}
                    className={note.pinned ? "" : "opacity-30 hover:opacity-100"}
                  >
                    <Pin size={13} />
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(note.id); }}
                    aria-label="Supprimer"
                    className="opacity-30 hover:opacity-100"
                  >
                    <Trash2 size={13} />
                  </button>
                </span>
              </div>
              <p className="line-clamp-4 whitespace-pre-wrap text-xs opacity-70">{note.content}</p>
              {note.updated_at && (
                <p className="mt-2 text-[10px] opacity-40">{new Date(note.updated_at).toLocaleString("fr-FR")}</p>
              )}
            </button>
          ))}
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={(o) => { if (!o) closeDialog(); }} title={editing ? "Modifier la note" : "Nouvelle note"}>
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (!title.trim()) return;
            if (editing) {
              updateMutation.mutate({ id: editing.id, data: { title: title.trim(), content } });
            } else {
              createMutation.mutate({ title: title.trim(), content });
            }
          }}
        >
          <Input placeholder="Titre" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <textarea
            className="input min-h-[140px] w-full resize-y"
            style={{ background: "var(--bg)" }}
            placeholder="Contenu…"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <Button type="submit" className="w-full" disabled={!title.trim() || createMutation.isPending || updateMutation.isPending}>
            {editing ? "Enregistrer" : "Créer"}
          </Button>
        </form>
      </Dialog>
    </div>
  );
}
