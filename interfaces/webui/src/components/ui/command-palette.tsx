"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useStore, AppPage } from "@/lib/store";

const COMMANDS: { id: string; label: string; icon: string; page?: AppPage; action?: () => void }[] = [
  { id: "mc", label: "Mission Control", icon: "◆", page: "mission-control" },
  { id: "goals", label: "Goals & Missions", icon: "◎", page: "goals" },
  { id: "memory", label: "Memory Explorer", icon: "◈", page: "memory" },
  { id: "skills", label: "Skills Lab", icon: "⚙", page: "skills" },
  { id: "monitor", label: "System Monitor", icon: "◉", page: "monitor" },
  { id: "approvals", label: "Approvals & Governance", icon: "⚠", page: "approvals" },
  { id: "chat", label: "Chat", icon: "💬", page: "chat" },
  { id: "new-goal", label: "Nouveau Goal", icon: "➕", page: "goals" },
  { id: "new-mission", label: "Nouvelle Mission", icon: "🚀", page: "goals" },
  { id: "new-skill", label: "Nouvelle Skill", icon: "🔧", page: "skills" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { setPage } = useStore();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((v) => !v);
        setQuery("");
        setSelected(0);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const filtered = query
    ? COMMANDS.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()))
    : COMMANDS;

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const execute = useCallback(
    (cmd: typeof COMMANDS[0]) => {
      if (cmd.page) setPage(cmd.page);
      if (cmd.action) cmd.action();
      setOpen(false);
      setQuery("");
    },
    [setPage]
  );

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelected((s) => Math.min(s + 1, filtered.length - 1));
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelected((s) => Math.max(s - 1, 0));
    }
    if (e.key === "Enter" && filtered[selected]) {
      execute(filtered[selected]);
    }
  };

  if (!open) return null;

  return (
    <div className="cmd-overlay" onClick={() => setOpen(false)}>
      <div className="cmd-modal" onClick={(e) => e.stopPropagation()}>
        <div className="cmd-input-row">
          <span className="cmd-prefix">▶</span>
          <input
            ref={inputRef}
            className="cmd-input"
            placeholder="Rechercher une action..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelected(0);
            }}
            onKeyDown={handleKey}
          />
        </div>
        <div className="cmd-results">
          {filtered.map((cmd, i) => (
            <button
              key={cmd.id}
              className={`cmd-item ${i === selected ? "cmd-selected" : ""}`}
              onClick={() => execute(cmd)}
              onMouseEnter={() => setSelected(i)}
            >
              <span className="cmd-icon">{cmd.icon}</span>
              <span className="cmd-label">{cmd.label}</span>
            </button>
          ))}
          {filtered.length === 0 && (
            <div className="cmd-empty">Aucun résultat pour "{query}"</div>
          )}
        </div>
        <div className="cmd-footer">
          <span>↑↓ Naviguer</span>
          <span>↵ Ouvrir</span>
          <span>Esc Fermer</span>
        </div>
      </div>
    </div>
  );
}