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
import { WebSocketConfigurationError, resolveTerminalWebSocketUrl as validateTerminalWebSocketUrl } from "@/lib/websocket-url";

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

/** URL WebSocket directe vers FastAPI, authentifiée par cookie HttpOnly. */
export function terminalSocketUrl(sessionId?: string): string {
  const explicitWebSocketUrl = process.env.NEXT_PUBLIC_WS_URL;
  const directApiUrl = process.env.NEXT_PUBLIC_ETHAN_API_URL;
  const isDevelopment = process.env.NODE_ENV !== "production" &&
    (typeof window === "undefined" || window.location.protocol !== "https:");
  let websocketOrigin: string | undefined;

  if (explicitWebSocketUrl && /^wss?:\/\//i.test(explicitWebSocketUrl)) {
    const parsed = new URL(explicitWebSocketUrl);
    websocketOrigin = `${parsed.protocol}//${parsed.host}`;
  } else if (directApiUrl && /^https?:\/\//i.test(directApiUrl)) {
    const parsed = new URL(directApiUrl);
    websocketOrigin = `${parsed.protocol === "https:" ? "wss://" : "ws://"}${parsed.host}`;
  } else if (isDevelopment) {
    websocketOrigin = "ws://localhost:8000";
  }

  if (!websocketOrigin) {
    throw new WebSocketConfigurationError(
      "NEXT_PUBLIC_WS_URL (or NEXT_PUBLIC_ETHAN_API_URL) must be configured in production.",
    );
  }

  const url = new URL(`${websocketOrigin}/v1/terminal/ws`);
  if (sessionId) url.searchParams.set("session_id", sessionId);
  if (/token=/i.test(url.toString())) {
    throw new WebSocketConfigurationError(
      "Terminal WebSocket URL must not contain a JWT.",
    );
  }
  const isSecurePage =
    typeof window !== "undefined" && window.location.protocol === "https:";
  const isProduction = process.env.NODE_ENV === "production" || isSecurePage;
  return validateTerminalWebSocketUrl(
    url.toString(),
    isProduction,
  );
}
