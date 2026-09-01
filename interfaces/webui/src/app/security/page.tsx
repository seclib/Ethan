"use client";

/**
 * Page Sécurité — 2FA (TOTP) et gestion des utilisateurs (admin).
 * Logique dans ETHAN Core (core/auth/totp.py) et table users PostgreSQL.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getTwoFactorStatus, setupTwoFactor, confirmTwoFactor, disableTwoFactor,
  listManagedUsers, createManagedUser, setUserActive,
  updateManagedUser, deleteManagedUser,
  getSecurityStatus, type SecurityStatusOverview, type ManagedUser,
} from "@/lib/api/security";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { ShieldCheck, ShieldOff, Users, Plus, UserCheck, UserX, Pencil, Trash2 } from "lucide-react";
import { AuditExplorer } from "./audit-explorer";
import { IdentityProviders } from "./identity-providers";

export default function SecurityPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [setupData, setSetupData] = React.useState<{ secret: string; uri: string } | null>(null);
  const [code, setCode] = React.useState("");
  const [newUsername, setNewUsername] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [newRole, setNewRole] = React.useState<"user" | "admin">("user");

  const { data: tfa } = useQuery({ queryKey: ["2fa"], queryFn: getTwoFactorStatus });
  const { data: users = [] } = useQuery({ queryKey: ["users"], queryFn: listManagedUsers, retry: false });
  const { data: sec } = useQuery({
    queryKey: ["security-status"],
    queryFn: getSecurityStatus,
    retry: false,
    staleTime: 30_000,
  });

  const invalidate = (k: string) => queryClient.invalidateQueries({ queryKey: [k] });

  const setupMutation = useMutation({
    mutationFn: setupTwoFactor,
    onSuccess: (d) => setSetupData({ secret: d.secret, uri: d.provisioning_uri }),
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  const confirmMutation = useMutation({
    mutationFn: () => confirmTwoFactor(code),
    onSuccess: () => {
      addToast({ type: "success", message: "2FA activée" });
      setSetupData(null); setCode(""); invalidate("2fa");
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Code invalide" }),
  });

  const disableMutation = useMutation({
    mutationFn: disableTwoFactor,
    onSuccess: () => { addToast({ type: "success", message: "2FA désactivée" }); invalidate("2fa"); },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  const createUserMutation = useMutation({
    mutationFn: () => createManagedUser({ username: newUsername.trim(), password: newPassword, role: newRole }),
    onSuccess: () => {
      addToast({ type: "success", message: `Utilisateur '${newUsername}' créé` });
      setNewUsername(""); setNewPassword(""); invalidate("users");
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  const activateMutation = useMutation({
    mutationFn: ({ username, active }: { username: string; active: boolean }) => setUserActive(username, active),
    onSuccess: () => invalidate("users"),
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  // ── Édition utilisateur (modale) — PUT /users/{username} ──
  const [editUser, setEditUser] = React.useState<ManagedUser | null>(null);
  const [editRole, setEditRole] = React.useState<"user" | "admin">("user");
  const [editActive, setEditActive] = React.useState(true);
  const [editPassword, setEditPassword] = React.useState("");

  const openEdit = (u: ManagedUser) => {
    setEditUser(u);
    setEditRole(u.roles.includes("admin") ? "admin" : "user");
    setEditActive(u.is_active);
    setEditPassword("");
  };

  const updateMutation = useMutation({
    mutationFn: () => {
      const data: { role?: "user" | "admin"; is_active?: boolean; password?: string } = {};
      const currentRole = editUser?.roles.includes("admin") ? "admin" : "user";
      if (editRole !== currentRole) data.role = editRole;
      if (editActive !== editUser?.is_active) data.is_active = editActive;
      if (editPassword.length > 0) data.password = editPassword;
      return updateManagedUser(editUser!.username, data);
    },
    onSuccess: (_d, _v) => {
      addToast({ type: "success", message: `Utilisateur '${editUser?.username}' mis à jour` });
      setEditUser(null); setEditPassword(""); invalidate("users");
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  // ── Suppression utilisateur (confirmation) — DELETE /users/{username} ──
  const [deleteTarget, setDeleteTarget] = React.useState<ManagedUser | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (username: string) => deleteManagedUser(username),
    onSuccess: (_d, username) => {
      addToast({ type: "success", message: `Utilisateur '${username}' supprimé` });
      setDeleteTarget(null); invalidate("users");
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center gap-2 px-4 py-3" style={{ background: "var(--panel)", borderBottom: "1px solid var(--border)" }}>
        <ShieldCheck size={18} className="text-accent" />
        <h1 className="text-base font-semibold">Sécurité</h1>
      </div>

      <div className="flex-1 space-y-6 overflow-auto p-4">
        {/* ── 2FA ── */}
        <section className="rounded-lg border p-4" style={{ background: "var(--panel)", borderColor: "var(--border)" }}>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Authentification à deux facteurs (TOTP)</h2>
            <span className="rounded-full px-2 py-0.5 text-[11px]"
              style={{ background: tfa?.enabled ? "var(--green-soft)" : "var(--muted)", color: tfa?.enabled ? "var(--green)" : "inherit" }}>
              {tfa?.enabled ? "Activée" : tfa?.pending ? "En attente" : "Désactivée"}
            </span>
          </div>

          {!tfa?.enabled && !setupData && (
            <Button size="sm" onClick={() => setupMutation.mutate()} disabled={setupMutation.isPending}>
              <ShieldCheck size={14} /> Activer la 2FA
            </Button>
          )}

          {setupData && !tfa?.enabled && (
            <div className="space-y-3">
              <p className="text-xs opacity-70">Scannez cette URI avec votre application authenticator (Aegis, Google Authenticator…) :</p>
              <code className="block break-all rounded p-2 text-[11px]" style={{ background: "var(--bg)", border: "1px solid var(--border)" }}>
                {setupData.uri}
              </code>
              <p className="text-xs opacity-70">Ou saisissez le secret manuellement : <code className="font-mono font-bold">{setupData.secret}</code></p>
              <div className="flex items-center gap-2">
                <Input placeholder="Code à 6 chiffres" value={code} onChange={(e) => setCode(e.target.value)} maxLength={6} className="w-40" />
                <Button size="sm" onClick={() => confirmMutation.mutate()} disabled={code.length !== 6 || confirmMutation.isPending}>
                  Confirmer
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setSetupData(null)}>Annuler</Button>
              </div>
            </div>
          )}

          {tfa?.enabled && (
            <Button size="sm" variant="ghost" onClick={() => disableMutation.mutate()} disabled={disableMutation.isPending}>
              <ShieldOff size={14} /> Désactiver la 2FA
            </Button>
          )}
        </section>

        {/* ── Utilisateurs ── */}
        <section className="rounded-lg border p-4" style={{ background: "var(--panel)", borderColor: "var(--border)" }}>
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold"><Users size={15} /> Utilisateurs</h2>

          <form className="mb-4 flex flex-wrap items-end gap-2" onSubmit={(e) => { e.preventDefault(); if (newUsername && newPassword.length >= 6) createUserMutation.mutate(); }}>
            <Input placeholder="Nom d'utilisateur" value={newUsername} onChange={(e) => setNewUsername(e.target.value)} className="w-48" required />
            <Input type="password" placeholder="Mot de passe (≥6)" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-48" required minLength={6} />
            <select value={newRole} onChange={(e) => setNewRole(e.target.value as "user" | "admin")}
              className="h-10 rounded-[var(--radius-sm)] border border-line-2 bg-background px-3 text-sm text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-accent/50">
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
            <Button type="submit" size="sm" disabled={!newUsername || newPassword.length < 6 || createUserMutation.isPending}>
              <Plus size={14} /> Créer
            </Button>
          </form>

          <div className="overflow-hidden rounded-lg" style={{ border: "1px solid var(--border)" }}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: "var(--muted)" }}>
                  <th className="px-3 py-2 text-left font-medium">Utilisateur</th>
                  <th className="px-3 py-2 text-left font-medium">Rôle</th>
                  <th className="px-3 py-2 text-left font-medium">2FA</th>
                  <th className="px-3 py-2 text-left font-medium">Statut</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} style={{ borderTop: "1px solid var(--border)" }}>
                    <td className="px-3 py-2 font-medium">{u.username}</td>
                    <td className="px-3 py-2 opacity-70">{u.roles.join(", ")}</td>
                    <td className="px-3 py-2">{u.totp_enabled ? "✓" : "—"}</td>
                    <td className="px-3 py-2">{u.is_active ? "Actif" : "Désactivé"}</td>
                    <td className="px-3 py-2 text-right">
                      <div className="inline-flex items-center gap-1">
                        <button
                          onClick={() => openEdit(u)}
                          aria-label={`Éditer ${u.username}`}
                          title="Éditer (rôle, statut, mot de passe)"
                          className="inline-flex opacity-50 hover:opacity-100"
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          onClick={() => activateMutation.mutate({ username: u.username, active: !u.is_active })}
                          aria-label={u.is_active ? "Désactiver" : "Activer"}
                          title={u.is_active ? "Désactiver" : "Activer"}
                          className="inline-flex opacity-50 hover:opacity-100"
                        >
                          {u.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                        </button>
                        <button
                          onClick={() => setDeleteTarget(u)}
                          aria-label={`Supprimer ${u.username}`}
                          title="Supprimer"
                          className="inline-flex opacity-50 hover:opacity-100 text-destructive"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── Modale d'édition utilisateur ── */}
        <Dialog
          open={editUser !== null}
          onClose={() => setEditUser(null)}
          title={`Éditer — ${editUser?.username ?? ""}`}
          size="sm"
        >
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-medium" htmlFor="edit-role">Rôle</label>
              <select
                id="edit-role"
                value={editRole}
                onChange={(e) => setEditRole(e.target.value as "user" | "admin")}
                className="h-9 w-full rounded-[var(--radius-sm)] border border-line-2 bg-background px-3 text-sm text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
              >
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
              {editUser?.roles.includes("admin") && editRole === "user" && (
                <p className="mt-1 text-[11px] text-amber-600">
                  Attention : impossible si c&apos;est le dernier admin actif.
                </p>
              )}
            </div>

            <div className="flex items-center justify-between">
              <label className="text-xs font-medium" htmlFor="edit-active">Compte actif</label>
              <input
                id="edit-active"
                type="checkbox"
                checked={editActive}
                onChange={(e) => setEditActive(e.target.checked)}
                className="h-4 w-4 accent-[var(--accent)]"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium" htmlFor="edit-password">
                Nouveau mot de passe <span className="opacity-50">(optionnel)</span>
              </label>
              <Input
                id="edit-password"
                type="password"
                placeholder="Laisser vide pour conserver"
                value={editPassword}
                onChange={(e) => setEditPassword(e.target.value)}
                minLength={6}
                className="w-full"
              />
              {editPassword.length > 0 && editPassword.length < 6 && (
                <p className="mt-1 text-[11px] text-destructive">6 caractères minimum.</p>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button size="sm" variant="ghost" onClick={() => setEditUser(null)}>Annuler</Button>
              <Button
                size="sm"
                disabled={
                  updateMutation.isPending ||
                  (editPassword.length > 0 && editPassword.length < 6)
                }
                onClick={() => updateMutation.mutate()}
              >
                Enregistrer
              </Button>
            </div>
          </div>
        </Dialog>

        {/* ── Confirmation de suppression ── */}
        <Dialog
          open={deleteTarget !== null}
          onClose={() => setDeleteTarget(null)}
          title="Supprimer l'utilisateur"
          size="sm"
        >
          <div className="space-y-4">
            <p className="text-sm">
              Supprimer définitivement le compte{' '}
              <span className="font-semibold">{deleteTarget?.username}</span> ?
              Cette action est irréversible.
            </p>
            <div className="flex justify-end gap-2">
              <Button size="sm" variant="ghost" onClick={() => setDeleteTarget(null)}>Annuler</Button>
              <Button
                size="sm"
                variant="destructive"
                disabled={deleteMutation.isPending}
                onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.username)}
              >
                Supprimer
              </Button>
            </div>
          </div>
        </Dialog>

        {/* ── ETHAN Security (lecture seule) ── */}
        <section className="rounded-lg border p-4" style={{ background: "var(--panel)", borderColor: "var(--border)" }}>
          <h2 className="mb-1 flex items-center gap-2 text-sm font-semibold"><ShieldCheck size={15} /> ETHAN Security</h2>
          <p className="mb-3 text-xs opacity-60">
            Représentation lecture seule — politiques, capacités et audit sont définis dans le Core (logique hors WebUI).
          </p>

          {!sec && (
            <p className="text-xs opacity-50">Indisponible — API hors ligne ou rôle non administrateur.</p>
          )}

          {sec && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {/* Politiques */}
              <div className="rounded-md border p-3" style={{ borderColor: "var(--border)" }}>
                <div className="text-[11px] font-semibold uppercase tracking-wide opacity-60">Policies</div>
                <div className="mt-1 text-2xl font-bold">{sec.policies.total}</div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {Object.entries(sec.policies.by_level).map(([level, n]) => (
                    <span key={level} className="rounded-full px-2 py-0.5 text-[11px]"
                      style={{ background: level === "CORE" ? "var(--green-soft)" : "var(--muted)",
                               color: level === "CORE" ? "var(--green)" : "inherit" }}>
                      {level}: {n}
                    </span>
                  ))}
                </div>
                <div className="mt-2 text-[11px] opacity-60">
                  {Object.entries(sec.policies.by_effect).map(([e, n]) => (
                    <span key={e} className="mr-2">· {e}: {n}</span>
                  ))}
                </div>
              </div>

              {/* Capacités */}
              <div className="rounded-md border p-3" style={{ borderColor: "var(--border)" }}>
                <div className="text-[11px] font-semibold uppercase tracking-wide opacity-60">Capabilities</div>
                <div className="mt-1 text-2xl font-bold">{sec.capabilities.active}</div>
                <div className="mt-2 text-[11px] opacity-60">
                  {sec.capabilities.subjects.length > 0
                    ? sec.capabilities.subjects.join(", ")
                    : "Aucune capability accordée"}
                </div>
                {sec.capabilities.summary && (
                  <div className="mt-2 text-[11px] opacity-60">
                    évaluations: {sec.capabilities.summary.total_evaluations} ·
                    allowed: {sec.capabilities.summary.allowed} ·
                    denied: {sec.capabilities.summary.denied}
                  </div>
                )}
              </div>

              {/* Audit */}
              <div className="rounded-md border p-3" style={{ borderColor: "var(--border)" }}>
                <div className="text-[11px] font-semibold uppercase tracking-wide opacity-60">Audit</div>
                <div className="mt-1 text-2xl font-bold">{sec.audit.total}</div>
                <div className="mt-2 text-[11px] opacity-60">
                  Journal append-only — traçabilité de chaque décision policy.
                </div>
              </div>
            </div>
          )}
        </section>

        {/* ── Fournisseurs d'identité — SCIM / LDAP / OAuth (statut + config réelle) ── */}
        <IdentityProviders />

        {/* ── Journal d'audit — consultation réelle (/internal/audit/search) ── */}
        <AuditExplorer />

      </div>
    </div>
  );
}
