"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useStore, AppPage } from "@/lib/store";

const COMMANDS: { id: string; label: string; icon: string; page?: AppPage; action?: () => void }[] = [
  { id: "dashboard", label: "Dashboard", icon: "◉", page: "dashboard" },
  { id: "assistant", label: "Assistant", icon: "💬", page: "assistant" },
  { id: "knowledge", label: "Knowledge", icon: "◈", page: "knowledge" },
  { id: "memory", label: "Memory", icon: "◆", page: "memory" },
  { id: "agents", label: "Agents", icon: "⚡", page: "agents" },
  { id: "planner", label: "Planner", icon: "📋", page: "planner" },
  { id: "models", label: "Models", icon: "🤖", page: "models" },
  { id: "providers", label: "Providers", icon: "🔌", page: "providers" },
  { id: "plugins", label: "Plugins", icon: "🧩", page: "plugins" },
  { id: "tools", label: "Tools", icon: "🛠", page: "tools" },
  { id: "documents", label: "Documents", icon: "📄", page: "documents" },
  { id: "settings", label: "Settings", icon: "⚙", page: "settings" },
  { id: "logs", label: "Logs", icon: "📜", page: "logs" },
  { id: "terminal", label: "Terminal", icon: "⌨", page: "terminal" },
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