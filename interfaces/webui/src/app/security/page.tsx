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
} from "@/lib/api/security";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ShieldCheck, ShieldOff, Users, Plus, UserCheck, UserX } from "lucide-react";

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

  return (
    <div className="flex h-full min-h-0 flex-col">
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
                      <button
                        onClick={() => activateMutation.mutate({ username: u.username, active: !u.is_active })}
                        aria-label={u.is_active ? "Désactiver" : "Activer"}
                        title={u.is_active ? "Désactiver" : "Activer"}
                        className="inline-flex opacity-50 hover:opacity-100"
                      >
                        {u.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
