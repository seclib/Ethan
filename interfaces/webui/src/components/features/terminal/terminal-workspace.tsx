"use client";

/**
 * TerminalWorkspace — l'écran « Terminal » du WebUI.
 *
 * Responsabilités (affichage + pilotage, aucune logique métier) :
 *  - ouvrir / fermer des sessions via l'API ;
 *  - tenir le WebSocket et refléter son état (connecté / reconnexion / erreur) ;
 *  - exposer utilisateur, machine, répertoire et état de connexion ;
 *  - proposer New session · Clear · Stop · Reconnect · Sessions.
 *
 * L'état de session (RUNNING/EXITED/…) vient TOUJOURS du Core ; l'interface
 * ne le devine jamais.
 */

import * as React from "react";
import { Button } from "@/components/ui/button";
import {
  closeTerminalSession,
  createTerminalSession,
  interruptTerminalSession,
  listTerminalSessions,
  terminalSocketUrl,
  type TerminalClientMessage,
  type TerminalServerMessage,
  type TerminalSession,
} from "@/lib/api/terminal";
import { TerminalView, type TerminalViewHandle } from "./terminal-view";

type ConnectionState = "idle" | "connecting" | "connected" | "reconnecting" | "error";

const STATUS_LABEL: Record<ConnectionState, string> = {
  idle: "aucune session",
  connecting: "connexion…",
  connected: "connecté",
  reconnecting: "reconnexion…",
  error: "erreur",
};

export function TerminalWorkspace() {
  const [session, setSession] = React.useState<TerminalSession | null>(null);
  const [sessions, setSessions] = React.useState<TerminalSession[]>([]);
  const [connection, setConnection] = React.useState<ConnectionState>("idle");
  const [error, setError] = React.useState<string | null>(null);
  const [showSessions, setShowSessions] = React.useState(false);

  const socketRef = React.useRef<WebSocket | null>(null);
  const listenersRef = React.useRef(
    new Set<(message: { type: string; data?: string }) => void>(),
  );
  const viewRef = React.useRef<TerminalViewHandle | null>(null);
  const reconnectRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const send = React.useCallback((message: TerminalClientMessage) => {
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    }
  }, []);

  const subscribe = React.useCallback(
    (listener: (message: { type: string; data?: string }) => void) => {
      listenersRef.current.add(listener);
      return () => {
        listenersRef.current.delete(listener);
      };
    },
    [],
  );

  const refreshSessions = React.useCallback(async () => {
    try {
      const data = await listTerminalSessions();
      setSessions(data.sessions ?? []);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  }, []);

  // ── Connexion WebSocket ──────────────────────────────────────────────────
  // `connect` se rappelle lui-même lors d'une reconnexion : la référence
  // indirecte évite une dépendance récursive dans le useCallback.
  const connectRef = React.useRef<
    ((sessionId?: string, reconnecting?: boolean) => void) | null
  >(null);

  const connect = React.useCallback(
    (sessionId?: string, reconnecting = false) => {
      setConnection(reconnecting ? "reconnecting" : "connecting");
      const socket = new WebSocket(terminalSocketUrl(sessionId));
      socketRef.current = socket;

      socket.onopen = () => setConnection("connected");

      socket.onmessage = (event) => {
        let message: TerminalServerMessage;
        try {
          message = JSON.parse(event.data) as TerminalServerMessage;
        } catch {
          return;
        }
        if (message.type === "session") {
          setSession(message as TerminalSession);
          void refreshSessions();
        }
        if (message.type === "exit") {
          setConnection("idle");
          void refreshSessions();
        }
        for (const listener of listenersRef.current) {
          listener(message as { type: string; data?: string });
        }
      };

      socket.onerror = () => {
        setConnection("error");
        setError("Connexion au terminal impossible (permission ou service indisponible).");
      };

      socket.onclose = (event) => {
        socketRef.current = null;
        // Une fermeture involontaire tente une reconnexion : fermer l'onglet
        // ne doit pas tuer le shell distant.
        if (event.code === 1000) {
          setConnection("idle");
          return;
        }
        setConnection("reconnecting");
        reconnectRef.current = setTimeout(() => connectRef.current?.(sessionId, true), 1500);
      };
    },
    [refreshSessions],
  );

  React.useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  // ── Actions ─────────────────────────────────────────────────────────────────
  const startSession = React.useCallback(async () => {
    setError(null);
    socketRef.current?.close();
    try {
      const created = await createTerminalSession();
      setSession(created);
      connect(created.id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      setConnection("error");
    }
  }, [connect]);

  const closeSession = React.useCallback(async () => {
    const current = session;
    socketRef.current?.close();
    socketRef.current = null;
    setSession(null);
    setConnection("idle");
    if (current) {
      try {
        await closeTerminalSession(current.id);
      } catch {
        // La session peut déjà avoir disparu (shell exit) : sans conséquence.
      }
    }
    void refreshSessions();
  }, [refreshSessions, session]);

  const interrupt = React.useCallback(() => {
    if (session) {
      void interruptTerminalSession(session.id).catch(() => send({ type: "interrupt" }));
    } else {
      send({ type: "interrupt" });
    }
  }, [send, session]);

  const reconnect = React.useCallback(() => {
    if (!session) {
      void startSession();
      return;
    }
    socketRef.current?.close();
    connect(session.id, true);
  }, [connect, session, startSession]);

  React.useEffect(() => {
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      // On NE ferme PAS la session au démontage : le shell continue côté Core
      // et l'utilisateur la retrouve dans la liste des sessions.
      socketRef.current?.close();
    };
  }, []);

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--fg)" }}>
            Terminal
          </h1>
          <p className="text-sm" style={{ color: "var(--fg-2)" }}>
            Sessions PTY servies par ETHAN Core — même backend que{" "}
            <code className="rounded bg-elevated px-1">interfaces/cli</code>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" variant="default" onClick={() => void startSession()}>
            Nouvelle session
          </Button>
          <Button size="sm" variant="outline" onClick={() => viewRef.current?.clear()}>
            Clear
          </Button>
          <Button size="sm" variant="outline" onClick={interrupt}>
            Stop
          </Button>
          <Button size="sm" variant="outline" onClick={reconnect}>
            Reconnect
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setShowSessions((value) => !value);
              void refreshSessions();
            }}
          >
            Sessions
          </Button>
          <Button size="sm" variant="destructive" onClick={() => void closeSession()}>
            Fermer
          </Button>
        </div>
      </header>

      <div
        className="flex flex-wrap items-center gap-4 rounded-[var(--radius-sm)] border px-3 py-2 text-xs"
        style={{ borderColor: "var(--line-2)", color: "var(--fg-2)" }}
      >
        <span>utilisateur : {session?.user ?? "—"}</span>
        <span>machine : {session?.hostname ?? "—"}</span>
        <span>répertoire : {session?.cwd ?? "—"}</span>
        <span>
          connexion : {STATUS_LABEL[connection]}
          {session ? ` · session ${session.state}` : ""}
        </span>
      </div>

      {error ? (
        <p className="text-xs" style={{ color: "var(--error-500, #e05252)" }}>
          {error}
        </p>
      ) : null}

      {showSessions ? (
        <ul
          className="max-h-40 overflow-auto rounded-[var(--radius-sm)] border p-2 text-xs"
          style={{ borderColor: "var(--line-2)", color: "var(--fg-2)" }}
        >
          {sessions.length === 0 ? (
            <li>Aucune session active.</li>
          ) : (
            sessions.map((entry) => (
              <li key={entry.id} className="flex items-center justify-between gap-3 py-1">
                <span>
                  {entry.id} · {entry.user} · {entry.cwd} · {entry.state}
                </span>
                <Button size="sm" variant="ghost" onClick={() => connect(entry.id)}>
                  Attacher
                </Button>
              </li>
            ))
          )}
        </ul>
      ) : null}

      <div
        className="min-h-0 flex-1 overflow-hidden rounded-[var(--radius-sm)] border"
        style={{ borderColor: "var(--line-2)" }}
      >
        <TerminalView
          ref={viewRef}
          sessionId={session?.id ?? null}
          subscribe={subscribe}
          onInput={(data) => send({ type: "input", data })}
          onResize={(cols, rows) => send({ type: "resize", cols, rows })}
        />
      </div>
    </div>
  );
}