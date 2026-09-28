"use client";

/**
 * ChannelsWorkspace — canaux de discussion persistés par ETHAN Core
 * (ChannelStore, core/state/channels.py ; routes /v1/channels).
 *
 * Création/suppression de canaux, lecture du fil et envoi d'un message.
 * Chaque écriture est arbitrée par le Core, qui publie l'événement
 * correspondant sur le bus (`channel.created`, `channel.message`…) : le
 * Runtime et les autres interfaces voient exactement les mêmes canaux.
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  listChannels,
  createChannel,
  deleteChannel,
  listChannelMessages,
  addChannelMessage,
  type Channel,
  type ChannelMessageRole,
} from "@/lib/api/channels";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog } from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { AlertCircle, Loader2, MessagesSquare, Plus, Send, Trash2 } from "lucide-react";

const ROLES: { id: ChannelMessageRole; label: string }[] = [
  { id: "user", label: "Utilisateur" },
  { id: "assistant", label: "Assistant" },
  { id: "system", label: "Système" },
  { id: "agent", label: "Agent" },
];

export function ChannelsWorkspace() {
  const addToast = useUIStore((s) => s.addToast);
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [confirmChannel, setConfirmChannel] = React.useState<Channel | null>(null);
  const [draft, setDraft] = React.useState("");
  const [role, setRole] = React.useState<ChannelMessageRole>("user");
  const [sending, setSending] = React.useState(false);

  const {
    data: channels = [],
    isLoading,
    error,
    refetch,
  } = useQuery({ queryKey: ["channels"], queryFn: () => listChannels(), retry: false });

  const selected = channels.find((c) => c.id === selectedId) ?? null;

  const messagesQuery = useQuery({
    queryKey: ["channel-messages", selectedId],
    queryFn: () => listChannelMessages(selectedId as string),
    enabled: selectedId !== null,
    retry: false,
  });
  const messages = React.useMemo(
    () =>
      [...(messagesQuery.data ?? [])].sort((a, b) =>
        (a.created_at || "").localeCompare(b.created_at || ""),
      ),
    [messagesQuery.data],
  );

  const handleCreate = async () => {
    setSaving(true);
    setFormError(null);
    try {
      const channel = await createChannel({ name, description });
      addToast({ type: "success", message: `Canal « ${channel.name} » créé` });
      setDialogOpen(false);
      setName("");
      setDescription("");
      await refetch();
      setSelectedId(channel.id);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Création refusée par le Core");
    } finally {
      setSaving(false);
    }
  };

  const handleSend = async () => {
    if (!selectedId || !draft.trim()) return;
    setSending(true);
    try {
      await addChannelMessage(selectedId, { content: draft, role });
      setDraft("");
      await messagesQuery.refetch();
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Envoi refusé par le Core",
      });
    } finally {
      setSending(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmChannel) return;
    try {
      await deleteChannel(confirmChannel.id);
      addToast({ type: "success", message: `Canal « ${confirmChannel.name} » supprimé` });
      if (selectedId === confirmChannel.id) setSelectedId(null);
      await refetch();
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Suppression refusée",
      });
    } finally {
      setConfirmChannel(null);
    }
  };

  return (
    <div className="flex h-full min-h-0">
      {/* Liste des canaux (persistés par le Core) */}
      <div
        className="flex w-64 shrink-0 flex-col border-r border-line-1"
        style={{ background: "var(--panel)" }}
      >
        <div className="flex items-center justify-between border-b border-line-1 px-4 py-3">
          <div className="flex items-center gap-2">
            <MessagesSquare className="h-4 w-4 text-muted-foreground" />
            <h1 className="text-sm font-semibold text-foreground">Channels</h1>
          </div>
          <Button size="sm" variant="ghost" title="Nouveau canal" onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {isLoading && (
            <div className="flex items-center gap-2 px-2 py-1 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" /> Chargement…
            </div>
          )}

          {error && (
            <div className="rounded-md border border-red-soft bg-red-soft p-2 text-xs text-red">
              <div className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                Impossible de charger les canaux
              </div>
              <Button size="sm" variant="outline" className="mt-2" onClick={() => refetch()}>
                Réessayer
              </Button>
            </div>
          )}

          {!isLoading && !error && channels.length === 0 && (
            <p className="px-2 py-3 text-xs text-muted-foreground">
              Aucun canal — les canaux et leurs messages sont persistés par ETHAN Core
              (ChannelStore).
            </p>
          )}

          {channels.map((channel) => (
            <button
              key={channel.id}
              onClick={() => setSelectedId(channel.id)}
              className={`flex w-full flex-col items-start rounded-md px-3 py-2 text-left transition-colors ${
                selectedId === channel.id
                  ? "bg-[var(--accent)]/10 text-foreground"
                  : "text-foreground-secondary hover:bg-[var(--panel-hover)]"
              }`}
            >
              <span className="w-full truncate text-sm">{channel.name}</span>
              {channel.description && (
                <span className="w-full truncate text-xs text-muted-foreground">
                  {channel.description}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Fil du canal sélectionné */}
      <div className="flex min-w-0 flex-1 flex-col">
        {selected ? (
          <>
            <div
              className="flex items-center justify-between gap-3 border-b border-line-1 px-4 py-3"
              style={{ background: "var(--panel)" }}
            >
              <div className="min-w-0">
                <h2 className="truncate text-sm font-semibold text-foreground">{selected.name}</h2>
                <p className="truncate text-xs text-muted-foreground">
                  {selected.description || "Canal Core — chaque message publie channel.message sur le bus."}
                </p>
              </div>
              <Button size="sm" variant="ghost" onClick={() => setConfirmChannel(selected)}>
                <Trash2 className="h-4 w-4" /> Supprimer
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {messagesQuery.isLoading && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Chargement des messages…
                </div>
              )}

              {messagesQuery.error && (
                <div className="rounded-lg border border-red-soft bg-red-soft p-4 text-sm text-red">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    Impossible de charger les messages
                  </div>
                  <p className="mt-1 text-xs">
                    {messagesQuery.error instanceof Error
                      ? messagesQuery.error.message
                      : "Core indisponible"}
                  </p>
                  <Button
                    size="sm"
                    variant="outline"
                    className="mt-3"
                    onClick={() => messagesQuery.refetch()}
                  >
                    Réessayer
                  </Button>
                </div>
              )}

              {!messagesQuery.isLoading && !messagesQuery.error && messages.length === 0 && (
                <p className="text-sm text-muted-foreground">Aucun message dans ce canal.</p>
              )}

              <div className="space-y-2">
                {messages.map((message) => (
                  <div key={message.id} className="rounded-lg border border-line-1 p-3">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span className="font-medium text-foreground-secondary">{message.role}</span>
                      <span>{message.user_id}</span>
                      <span>{new Date(message.created_at).toLocaleString()}</span>
                    </div>
                    <p className="mt-1 whitespace-pre-wrap text-sm text-foreground">
                      {message.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-line-1 p-3" style={{ background: "var(--panel)" }}>
              <div className="flex items-center gap-2">
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as ChannelMessageRole)}
                  aria-label="Rôle du message"
                  className="rounded-md border border-line-1 bg-[var(--panel)] px-2 py-2 text-xs text-foreground"
                >
                  {ROLES.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.label}
                    </option>
                  ))}
                </select>
                <Textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Écrire un message…"
                  rows={2}
                  className="flex-1"
                />
                <Button onClick={handleSend} disabled={sending || !draft.trim()}>
                  {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  Envoyer
                </Button>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Le message est écrit par le Core (ChannelStore) puis publié sur le bus —
                aucune copie locale dans la WebUI.
              </p>
            </div>
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center p-6 text-center text-sm text-muted-foreground">
            Sélectionnez un canal pour lire et publier ses messages.
          </div>
        )}
      </div>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} title="Nouveau canal" size="sm">
        <div className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Nom</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="ex: équipe-core"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Description</label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          {formError && <p className="text-sm text-red">{formError}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setDialogOpen(false)}>
              Annuler
            </Button>
            <Button onClick={handleCreate} disabled={saving || !name.trim()}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Créer
            </Button>
          </div>
        </div>
      </Dialog>

      <ConfirmDialog
        open={confirmChannel !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmChannel(null);
        }}
        title="Supprimer ce canal ?"
        message={
          confirmChannel
            ? `« ${confirmChannel.name} » et ses messages seront supprimés du Core.`
            : undefined
        }
        confirmLabel="Supprimer"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  );
}
