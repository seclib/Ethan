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
