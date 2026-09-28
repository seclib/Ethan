"use client";

/**
 * ETHAN WebUI — Connections API service
 *
 * Client HTTP fin sur les routes /connections de l'API ETHAN
 * (interfaces/api/routers/connections.py), qui délèguent au ConnectionManager
 * du Core (core/integrations/connections). Aucune logique métier ici : le
 * WebUI affiche et envoie des actions ; le Core possède toute la logique
 * OAuth, des tokens, des statuts et permissions.
 *
 * Sécurité (repo-wide) :
 *  - Aucune route n'expose un token ; `connection-tokens` n'est lisible que par
 *    le Core/Runtime. Les enregistrements publics (`connections`) excluent
 *    `state` et `state_expires_at`.
 *  - Aucun `client_secret`/`access_token` ne passe jamais dans ce client : le
 *    seul secret résolu côté Core vient du SecretManager (env/Vault).
 *  - Le WebUI reçoit une `authorization_url` (contient `client_id`, public par
 *    conception OAuth) àouvrir dans un nouvel onglet ; le callback OAuth revient
 *    au Core, jamais au frontend.
 */

import { apiFetch } from "@/lib/api/client";

/** Scope OAuth demandé/expliqué — défini EXPLICITEMENT par le Core. */
export interface ScopeSpec {
  scope: string;
  summary: string;
  /** true → donnée sensible ; justifie l'explication contextuelle. */
  sensitive: boolean;
}

/** Catalogue des connecteurs (sans aucune donnée utilisateur). */
export interface ConnectionCatalog {
  id: string;
  label: string;
  description: string;
  scopes: ScopeSpec[];
}

/** Connexion utilisateur — VUE PUBLIQUE (jamais de token/state). */
export interface Connection {
  id: string;
  provider: string;
  user_id: string;
  status: "pending" | "connected" | "disconnected" | "error";
  connected_at: string | null;
  updated_at: string;
  scopes_requested: string[];
  scopes_granted: string[] | null;
  token_expires_at: number | null;
  /** Identité diste NON SECRÈTE (login, email, workspace) — publique. */
  account: Record<string, unknown>;
  last_error: string | null;
}

/** Réponse de start() : l'URL d'autorisation à ouvrir dans un nouvel onglet. */
export interface ConnectionStart {
  connection_id: string;
  provider: string;
  authorization_url: string;
  state: string;
  scopes_requested: string[];
}

interface ReconnectData { reconnect?: boolean; redirect_uri?: string }

/* ── Catalogue ─────────────────────────────────────────────────────────── */

export function listProviders(): Promise<ConnectionCatalog[]> {
  return apiFetch<ConnectionCatalog[]>("/connections/providers");
}

/* ── Connexions utilisateur ────────────────────────────────────────────── */

export function listConnections(): Promise<Connection[]> {
  return apiFetch<Connection[]>("/connections");
}

export function getConnection(provider: string): Promise<Connection | null> {
  return apiFetch<Connection | null>(`/connections/${encodeURIComponent(provider)}`);
}

/* ── Lifecycle (mutations Core-only — RBAC PLUGINS) ────────────────────── */

export async function connect(provider: string): Promise<ConnectionStart> {
  return apiFetch<ConnectionStart>(
    `/connections/${encodeURIComponent(provider)}/connect`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export async function reconnect(provider: string): Promise<ConnectionStart> {
  const data: ReconnectData = { reconnect: true };
  return apiFetch<ConnectionStart>(
    `/connections/${encodeURIComponent(provider)}/connect`,
    { method: "POST", body: JSON.stringify(data) },
  );
}

export async function testConnection(provider: string): Promise<Connection> {
  return apiFetch<Connection>(
    `/connections/${encodeURIComponent(provider)}/test`,
    { method: "POST" },
  );
}

export interface ConnectionPermissions {
  provider: string;
  connection_id: string;
  requested: ScopeSpec[];
  granted: string[];
}

export function getPermissions(provider: string): Promise<ConnectionPermissions> {
  return apiFetch<ConnectionPermissions>(
    `/connections/${encodeURIComponent(provider)}/permissions`,
  );
}

export async function disconnect(provider: string): Promise<Connection> {
  return apiFetch<Connection>(`/connections/${encodeURIComponent(provider)}`, {
    method: "DELETE",
  });
}

export type { ConnectionStart as ConnectResult };
