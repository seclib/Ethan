"use client";

/**
 * Page Groups — administration des groupes ETHAN (admin).
 *
 * Toutes les opérations passent par les routes /groups de l'API ETHAN
 * (interfaces/api/routers/domains.py), qui délègent au GroupManager du Core
 * (core/auth/groups.py). Aucune logique métier ici : sérialisation, appels,
 * affichage. Patterns repris de la page Sécurité (react-query, Dialogs,
 * toasts).
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listGroups, createGroup, updateGroup, deleteGroup,
  addGroupMember, removeGroupMember, type EthGroup,
} from "@/lib/api/groups";
import { listManagedUsers, type ManagedUser } from "@/lib/api/security";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import { FolderKanban, Plus, Pencil, Trash2, UserPlus, UserMinus } from "lucide-react";

export default function GroupsPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data: groups = [], isLoading, error } = useQuery({
    queryKey: ["groups"],
    queryFn: listGroups,
    retry: false,
  });
  const { data: users = [] } = useQuery({
    queryKey: ["users"],
    queryFn: listManagedUsers,
    retry: false,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["groups"] });

  // ── Création (POST /groups) ──
  const [createOpen, setCreateOpen] = React.useState(false);
  const [newName, setNewName] = React.useState("");
  const [newDescription, setNewDescription] = React.useState("");
  const createMutation = useMutation({
    mutationFn: () => createGroup({ name: newName.trim(), description: newDescription.trim() }),
    onSuccess: () => {
      addToast({ type: "success", message: `Groupe '${newName.trim()}' créé` });
      setCreateOpen(false); setNewName(""); setNewDescription(""); invalidate();
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  // ── Édition (PUT /groups/{id}) ──
  const [editGroup, setEditGroup] = React.useState<EthGroup | null>(null);
  const [editName, setEditName] = React.useState("");
  const [editDescription, setEditDescription] = React.useState("");
  const openEdit = (g: EthGroup) => {
    setEditGroup(g); setEditName(g.name); setEditDescription(g.description || "");
  };
  const updateMutation = useMutation({
    mutationFn: () => {
      const data: { name?: string; description?: string } = {};
      if (editName.trim() && editName.trim() !== editGroup?.name) data.name = editName.trim();
      if ((editDescription.trim() || "") !== (editGroup?.description || "")) data.description = editDescription.trim();
      return updateGroup(editGroup!.id, data);
    },
    onSuccess: () => {
      addToast({ type: "success", message: `Groupe '${editName.trim()}' mis à jour` });
      setEditGroup(null); invalidate();
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  // ── Suppression (DELETE /groups/{id}) avec confirmation ──
  const [deleteTarget, setDeleteTarget] = React.useState<EthGroup | null>(null);
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteGroup(id),
    onSuccess: () => {
      addToast({ type: "success", message: "Groupe supprimé" });
      setDeleteTarget(null); invalidate();
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  // ── Membres (POST/DELETE /groups/{id}/members/{user_id}) ──
  const [membersGroup, setMembersGroup] = React.useState<EthGroup | null>(null);
  const [memberToAdd, setMemberToAdd] = React.useState("");
  const addMemberMutation = useMutation({
    mutationFn: () => addGroupMember(membersGroup!.id, memberToAdd),
    onSuccess: (g) => {
      addToast({ type: "success", message: "Membre ajouté" });
      setMemberToAdd(""); setMembersGroup(g); invalidate();
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });
  const removeMemberMutation = useMutation({
    mutationFn: (userId: string) => removeGroupMember(membersGroup!.id, userId),
    onSuccess: (g) => {
      addToast({ type: "success", message: "Membre retiré" });
      setMembersGroup(g); invalidate();
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  const availableUsers = users.filter(
    (u: ManagedUser) => !(membersGroup?.members ?? []).includes(u.username),
  );

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center justify-between gap-2 px-4 py-3" style={{ background: "var(--panel)", borderBottom: "1px solid var(--border)" }}>
        <div className="flex items-center gap-2">
          <FolderKanban size={18} className="text-accent" />
          <h1 className="text-base font-semibold">Groupes</h1>
        </div>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus size={14} /> Nouveau groupe
        </Button>
      </div>

      <div className="flex-1 space-y-4 overflow-auto p-4">
        {isLoading ? (
          <div className="flex justify-center p-10"><Spinner /></div>
        ) : error ? (
          <p className="text-sm text-destructive">
            Impossible de charger les groupes : {error instanceof Error ? error.message : "erreur inconnue"}
          </p>
        ) : groups.length === 0 ? (
          <div className="rounded-lg border border-dashed p-10 text-center" style={{ borderColor: "var(--border)" }}>
            <FolderKanban size={32} className="mx-auto mb-3 text-foreground-tertiary" />
            <p className="text-sm text-foreground-secondary">Aucun groupe.</p>
            <p className="text-xs text-foreground-tertiary mt-1">
              Créez un groupe pour organiser les permissions des utilisateurs.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {groups.map((g) => (
              <div
                key={g.id}
                className="rounded-lg border p-4 flex items-center justify-between gap-4"
                style={{ background: "var(--panel)", borderColor: "var(--border)" }}
              >
                <div className="min-w-0">
                  <p className="text-sm font-semibold truncate">{g.name}</p>
                  <p className="text-xs text-foreground-tertiary truncate">
                    {g.description || "Pas de description"}
                  </p>
                  <p className="text-[10px] text-foreground-tertiary mt-1">
                    {g.members.length} membre{g.members.length > 1 ? "s" : ""}
                  </p>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <Button variant="ghost" size="sm" onClick={() => setMembersGroup(g)} title="Gérer les membres">
                    <UserPlus size={14} /> Membres
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => openEdit(g)} title="Modifier">
                    <Pencil size={14} />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(g)} title="Supprimer" className="text-destructive hover:bg-destructive/10">
                    <Trash2 size={14} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Création */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="Nouveau groupe">
        <div className="space-y-3">
          <Input placeholder="Nom du groupe" value={newName} onChange={(e) => setNewName(e.target.value)} />
          <Input placeholder="Description (optionnel)" value={newDescription} onChange={(e) => setNewDescription(e.target.value)} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setCreateOpen(false)}>Annuler</Button>
            <Button size="sm" disabled={!newName.trim() || createMutation.isPending} onClick={() => createMutation.mutate()}>
              Créer
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Édition */}
      <Dialog open={!!editGroup} onClose={() => setEditGroup(null)} title={`Modifier « ${editGroup?.name} »`}>
        <div className="space-y-3">
          <Input placeholder="Nom" value={editName} onChange={(e) => setEditName(e.target.value)} />
          <Input placeholder="Description" value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setEditGroup(null)}>Annuler</Button>
            <Button size="sm" disabled={updateMutation.isPending} onClick={() => updateMutation.mutate()}>Enregistrer</Button>
          </div>
        </div>
      </Dialog>

      {/* Suppression */}
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Supprimer le groupe">
        <p className="text-sm text-foreground-secondary">
          Supprimer définitivement <span className="font-semibold">{deleteTarget?.name}</span> ?
          Les {deleteTarget?.members.length ?? 0} membre(s) perdront les permissions associées.
        </p>
        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" size="sm" onClick={() => setDeleteTarget(null)}>Annuler</Button>
          <Button
            variant="destructive" size="sm"
            disabled={deleteMutation.isPending}
            onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
          >
            Supprimer
          </Button>
        </div>
      </Dialog>

      {/* Membres */}
      <Dialog open={!!membersGroup} onClose={() => setMembersGroup(null)} title={`Membres — ${membersGroup?.name ?? ""}`} size="lg">
        <div className="space-y-4">
          <div className="flex gap-2">
            <select
              value={memberToAdd}
              onChange={(e) => setMemberToAdd(e.target.value)}
              className="flex-1 rounded-md border bg-bg-2 px-2 py-1.5 text-sm text-foreground"
              style={{ borderColor: "var(--border)" }}
              aria-label="Utilisateur à ajouter"
            >
              <option value="">— Choisir un utilisateur —</option>
              {availableUsers.map((u) => (
                <option key={u.username} value={u.username}>{u.username}</option>
              ))}
            </select>
            <Button
              size="sm" disabled={!memberToAdd || addMemberMutation.isPending}
              onClick={() => addMemberMutation.mutate()}
            >
              <UserPlus size={14} /> Ajouter
            </Button>
          </div>

          {(membersGroup?.members.length ?? 0) === 0 ? (
            <p className="text-xs text-foreground-tertiary text-center py-4">Aucun membre.</p>
          ) : (
            <ul className="space-y-1">
              {membersGroup!.members.map((m) => (
                <li key={m} className="flex items-center justify-between rounded-md border px-3 py-2" style={{ borderColor: "var(--border)" }}>
                  <span className="text-sm">{m}</span>
                  <Button
                    variant="ghost" size="sm" className="text-destructive hover:bg-destructive/10"
                    title="Retirer du groupe" disabled={removeMemberMutation.isPending}
                    onClick={() => removeMemberMutation.mutate(m)}
                  >
                    <UserMinus size={14} />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Dialog>
    </div>
  );
}
