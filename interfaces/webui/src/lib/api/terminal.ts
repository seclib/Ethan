"use client";

/**
 * ETHAN WebUI — client du terminal.
 *
 * Passerelle mince vers l'API `/v1/terminal` (elle-même une passerelle vers
 * `core/terminal`). Ce fichier ne contient AUCUNE logique de terminal : il
 * sérialise les requêtes et expose le vocabulaire du Core tel quel.
 *
 * Cohérence (AGENTS.md) : une commande ETHAN tapee dans ce terminal passe par
 * le MÊME backend que `interfaces/cli/` — la WebUI ne duplique rien.
 */

import { apiFetch } from "@/lib/api/client";

/** États d'une session — vocabulaire Core, jamais traduit. */
export type TerminalState = "RUNNING" | "EXITED" | "CLOSED" | "ERROR";

/** Une session terminal telle que le Core la décrit. */
export interface TerminalSession {
  id: string;
  user: string;
  cwd: string;
  state: TerminalState;
  pid: number;
  exit_code: number | null;
  created_at: number;
  last_activity: number;
  cols: number;
  rows: number;
  hostname: string;
  permission: string;
}

/** Messages client → serveur. */
export type TerminalClientMessage =
  | { type: "input"; data: string }
  | { type: "resize"; cols: number; rows: number }
  | { type: "interrupt" }
  | { type: "ping" };

/** Messages serveur → client. */
export type TerminalServerMessage =
  | ({ type: "session" } & TerminalSession)
  | { type: "output"; data: string }
  | { type: "exit"; exit_code: number | null }
  | { type: "error"; code: string; detail: string }
  | { type: "pong" };

export function listTerminalSessions(): Promise<{ sessions: TerminalSession[] }> {
  return apiFetch("/v1/terminal/sessions");
}

export function createTerminalSession(params?: {
  cwd?: string;
  cols?: number;
  rows?: number;
}): Promise<TerminalSession> {
  return apiFetch("/v1/terminal/sessions", {
    method: "POST",
    body: JSON.stringify(params ?? {}),
  });
}

export function closeTerminalSession(sessionId: string): Promise<TerminalSession> {
  return apiFetch(`/v1/terminal/sessions/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
}

export function interruptTerminalSession(sessionId: string): Promise<{ status: string }> {
  return apiFetch(`/v1/terminal/sessions/${encodeURIComponent(sessionId)}/interrupt`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

/** URL du WebSocket, avec le JWT (la WS n'est pas couverte par le middleware HTTP). */
export function terminalSocketUrl(sessionId?: string): string {
  const base = process.env.NEXT_PUBLIC_ETHAN_API_URL ?? "/api";
  const httpBase = base.startsWith("http") ? base : `${window.location.origin}${base}`;
  const url = new URL(`${httpBase.replace(/^http/, "ws")}/v1/terminal/ws`);

  const token =
    (typeof window !== "undefined" && localStorage.getItem("ethan_token")) || "";
  if (token) url.searchParams.set("token", token);
  if (sessionId) url.searchParams.set("session_id", sessionId);
  return url.toString();
}