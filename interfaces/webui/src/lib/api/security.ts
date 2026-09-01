"use client";

/**
 * ETHAN WebUI — Security & user management client.
 * Business logic lives in ETHAN Core (core/auth/totp.py) and the
 * PostgreSQL users table; this client only serialises requests.
 */

import { apiFetch } from "@/lib/api/client";

// ── Types ────────────────────────────────────────────────────────────────

export interface TwoFactorStatus {
  enabled: boolean;
  pending: boolean;
}

export interface TwoFactorSetup {
  enabled: false;
  secret: string;
  provisioning_uri: string;
}

export interface ManagedUser {
  id: string;
  username: string;
  roles: string[];
  is_active: boolean;
  totp_enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

// ── 2FA (TOTP) ──────────────────────────────────────────────────────────

export async function getTwoFactorStatus(): Promise<TwoFactorStatus> {
  return apiFetch<TwoFactorStatus>("/auth/2fa/status");
}

export async function setupTwoFactor(): Promise<TwoFactorSetup> {
  return apiFetch<TwoFactorSetup>("/auth/2fa/setup", { method: "POST" });
}

export async function confirmTwoFactor(code: string): Promise<{ enabled: boolean; status: string }> {
  return apiFetch("/auth/2fa/confirm", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export async function disableTwoFactor(): Promise<{ enabled: boolean; status: string }> {
  return apiFetch("/auth/2fa/disable", { method: "POST" });
}

// ── Admin user management ───────────────────────────────────────────────

export async function listManagedUsers(): Promise<ManagedUser[]> {
  return apiFetch<ManagedUser[]>("/users");
}

// ── ETHAN Security overview (Phase 07, lecture seule) ──────────────────────

export interface SecurityStatusOverview {
  policies: {
    total: number;
    by_level: Record<string, number>;
    by_effect: Record<string, number>;
    categories: string[];
  };
  capabilities: {
    active: number;
    subjects: string[];
    summary?: { total_evaluations: number; allowed: number; denied: number };
  };
  audit: { total: number };
}

/**
 * Résumé lecture seule du système de sécurité ETHAN (policies / capabilities /
 * audit). Sert uniquement à la représentation — aucune action de mutation.
 */
export async function getSecurityStatus(): Promise<SecurityStatusOverview> {
  return apiFetch<SecurityStatusOverview>("/security/status");
}


export async function createManagedUser(data: {
  username: string;
  password: string;
  role: "user" | "admin";
}): Promise<ManagedUser> {
  return apiFetch<ManagedUser>("/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function setUserActive(username: string, isActive: boolean): Promise<{ username: string; is_active: boolean }> {
  return apiFetch(`/users/${encodeURIComponent(username)}/activate`, {
    method: "PUT",
    body: JSON.stringify({ is_active: isActive }),
  });
}

/**
 * Mise à jour admin d'un utilisateur (rôle, statut, mot de passe).
 * PUT /users/{username} — protections serveur : auto-démotion interdite,
 * dernier admin actif intouchable. Toutes les clés sont optionnelles.
 */
export async function updateManagedUser(
  username: string,
  data: { role?: "user" | "admin"; is_active?: boolean; password?: string },
): Promise<ManagedUser> {
  return apiFetch<ManagedUser>(`/users/${encodeURIComponent(username)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Suppression définitive d'un compte. DELETE /users/{username} — protections
 * serveur : auto-suppression interdite, dernier admin actif protégé.
 */
export async function deleteManagedUser(username: string): Promise<{ status: string; username: string }> {
  return apiFetch<{ status: string; username: string }>(
    `/users/${encodeURIComponent(username)}`,
    { method: "DELETE" },
  );
}

// ── Audit explorer (GET /internal/audit/search) ─────────────────────────

/**
 * Événement d'audit — sérialisation exacte de core/audit/types.py:AuditEntry.to_dict().
 * Aucune logique d'audit ici : lecture seule, la journalisation reste dans le Core.
 */
export interface AuditEvent {
  id: string;
  timestamp: string;
  category: string;
  decision: string;
  action: string;
  actor: string;
  source: string;
  details?: Record<string, unknown>;
  correlation_id?: string;
  tags?: string[];
}

/**
 * Recherche dans le journal d'audit. L'API impose `q` ≥ 1 caractère
 * (sous-chaîne sur action/actor/source/correlation_id/details) et plafonne
 * à 20 entrées, tri récent → ancien. Pas de pagination serveur : le tri,
 * les filtres et la pagination restent client-side dans l'explorateur.
 */
export async function searchAuditEvents(q: string): Promise<AuditEvent[]> {
  return apiFetch<AuditEvent[]>(
    `/internal/audit/search?q=${encodeURIComponent(q)}`,
  );
}
