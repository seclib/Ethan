"use client";

import { useEffect, useState, useCallback, useMemo } from "react";

export interface Command {
  id: string;
  kind: "nav" | "action" | "ask";
  title: string;
  sub?: string;
  glyph?: string;
  kbd?: string;
  group?: string;
  run: () => void;
}

export function useCommandPalette(commands: Command[]) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    const scored = commands
      .map((c) => {
        const text = (c.title + " " + (c.sub || "")).toLowerCase();
        let s = 0;
        if (text.includes(q)) s = 3;
        else {
          const words = q.split(" ").filter(Boolean);
          if (words.length && words.every((w) => text.includes(w))) s = 2;
          else {
            let qi = 0;
            for (let i = 0; i < text.length && qi < q.length; i++) {
              if (text[i] === q[qi]) qi++;
            }
            if (qi === q.length) s = 1;
          }
        }
        return { cmd: c, s };
      })
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s)
      .map((x) => x.cmd);
    return scored;
  }, [query, commands]);

  const groups = results.reduce<Record<string, Command[]>>((acc: Record<string, Command[]>, cmd: Command) => {
    const g = cmd.group || "Navigation";
    (acc[g] = acc[g] || []).push(cmd);
    return acc;
  }, {} as Record<string, Command[]>);

  const exec = useCallback(
    (idx: number) => {
      const cmd = results[idx];
      if (cmd) {
        cmd.run();
        setOpen(false);
        setQuery("");
      }
    },
    [results]
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        setOpen((v) => !v);
        setQuery("");
        setSelected(0);
      }
      if (!open) return;
      if (e.key === "Escape") {
        setOpen(false);
        setQuery("");
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelected((s) => Math.min(s + 1, results.length - 1));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelected((s) => Math.max(s - 1, 0));
      }
      if (e.key === "Enter") {
        e.preventDefault();
        exec(selected);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, results, selected, exec]);

  return { open, query, setQuery, selected, setSelected, results, groups, setOpen, exec };
}