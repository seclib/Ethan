"use client";

/**
 * TerminalView — rendu xterm d'une session PTY distante.
 *
 * Ce composant ne décide rien : il affiche les octets reçus du Core et
 * renvoie ce que l'utilisateur tape. Aucune logique de session n'est
 * réimplémentée côté WebUI (AGENTS.md — Première Loi).
 *
 * Rôles du composant, strictement iodique :
 *  - `xterm` affiche le flux ANSI (couleurs, contrôle du curseur) ;
 *  - la saisie clavier est envoyée en `input` (avec Ctrl+C et flèches) ;
 *  - le redimensionnement de la fenêtre est poussé en `resize` ;
 *  - les boutons Stop / Clear / Reconnect sont delegués au parent.
 */

import * as React from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";

export interface TerminalViewHandle {
  /** Vide l'écran local (le scrollback du terminal, pas le shell distant). */
  clear: () => void;
  /** Focus clavier sur le terminal. */
  focus: () => void;
}

interface TerminalViewProps {
  /** Écrit dans le PTY (stdin). */
  onInput: (data: string) => void;
  /** Redimensionne le PTY distant. */
  onResize: (cols: number, rows: number) => void;
  /** Session à rattacher au montage (reconnexion). */
  sessionId?: string | null;
  /** Le parent construit et owns le WebSocket : il transmet les messages. */
  subscribe: (listener: (message: { type: string; data?: string }) => void) => () => void;
  className?: string;
}

export const TerminalView = React.forwardRef<TerminalViewHandle, TerminalViewProps>(
  function TerminalView({ onInput, onResize, sessionId, subscribe }, ref) {
    const containerRef = React.useRef<HTMLDivElement | null>(null);
    const termRef = React.useRef<Terminal | null>(null);
    const fitRef = React.useRef<FitAddon | null>(null);
    const onInputRef = React.useRef(onInput);
    const onResizeRef = React.useRef(onResize);

    onInputRef.current = onInput;
    onResizeRef.current = onResize;

    React.useImperativeHandle(ref, () => ({
      clear: () => termRef.current?.clear(),
      focus: () => termRef.current?.focus(),
    }));

    // ── Montage du terminal xterm ──────────────────────────────────────────
    React.useEffect(() => {
      const container = containerRef.current;
      if (!container) return;

      const term = new Terminal({
        convertEol: true,
        cursorBlink: true,
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        fontSize: 13,
        theme: {
          background: "#0b0f14",
          foreground: "#d7dde5",
          cursor: "#7fd1c1",
          selectionBackground: "rgba(127, 209, 193, 0.3)",
        },
        scrollback: 5000,
      });
      const fit = new FitAddon();
      term.loadAddon(fit);
      term.open(container);
      fit.fit();

      termRef.current = term;
      fitRef.current = fit;

      const dataDisposable = term.onData((data) => {
        // Le PTY est en mode raw : `\x03` traverse la ligne discipline et devient
        // un SIGINT pour le groupe de processus — comme dans un terminal réel.
        // Appeler l'API en plus interromprait le processus deux fois. L'API
        // `interrupt` reste réservée au bouton Stop du parent.
        onInputRef.current(data);
      });

      const resizeObserver = new ResizeObserver(() => {
        try {
          fit.fit();
        } catch {
          return; // conteneur pas encore dimensionné
        }
        onResizeRef.current(term.cols, term.rows);
      });
      resizeObserver.observe(container);

      return () => {
        resizeObserver.disconnect();
        dataDisposable.dispose();
        term.dispose();
        termRef.current = null;
        fitRef.current = null;
      };
    }, []);

    // ── Reconnexion : on repart d'un écran propre ─────────────────────────
    React.useEffect(() => {
      termRef.current?.clear();
    }, [sessionId]);

    // ── Flux sortant du WebSocket → terminal ──────────────────────────────
    React.useEffect(() => {
      return subscribe((message) => {
        if (message.type === "output" && typeof message.data === "string") {
          termRef.current?.write(message.data);
        }
      });
    }, [subscribe]);

    return <div ref={containerRef} className="h-full w-full" data-testid="terminal-view" />;
  },
);