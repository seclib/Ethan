"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/stores/ui.store";
import { useAgentsStore } from "@/stores/agents.store";
import { useGoalsStore } from "@/stores/goals.store";
import { useMissionsStore } from "@/stores/missions.store";

interface Command {
  id: string;
  label: string;
  icon: string;
  category: "page" | "action" | "recent";
  action: () => void;
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const { closeCommandPalette, toggleSidebar, toggleInspector } = useUIStore();
  const { agents } = useAgentsStore();
  const { goals } = useGoalsStore();
  const { missions } = useMissionsStore();

  // Load recent commands from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("ethan:recent-commands");
    if (saved) {
      setRecentCommands(JSON.parse(saved));
    }
  }, []);

  // Save command to recent
  const saveToRecent = useCallback((commandId: string) => {
    setRecentCommands((prev) => {
      const updated = [commandId, ...prev.filter((id) => id !== commandId)].slice(0, 10);
      localStorage.setItem("ethan:recent-commands", JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Keyboard shortcuts
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

  // Build commands list
  const commands: Command[] = [
    // Pages
    { id: "page-dashboard", label: "Dashboard", icon: "◉", category: "page", action: () => { router.push("/"); saveToRecent("page-dashboard"); } },
    { id: "page-agents", label: "Agents", icon: "⚡", category: "page", action: () => { router.push("/agents"); saveToRecent("page-agents"); } },
    { id: "page-missions", label: "Missions", icon: "🎯", category: "page", action: () => { router.push("/missions"); saveToRecent("page-missions"); } },
    { id: "page-goals", label: "Goals", icon: "🏆", category: "page", action: () => { router.push("/goals"); saveToRecent("page-goals"); } },
    { id: "page-flux", label: "Event Flux", icon: "📊", category: "page", action: () => { router.push("/flux"); saveToRecent("page-flux"); } },
    { id: "page-memory", label: "Memory Facts", icon: "�", category: "page", action: () => { router.push("/memory/facts"); saveToRecent("page-memory"); } },
    { id: "page-skills", label: "Skills Lab", icon: "⚡", category: "page", action: () => { router.push("/skills/lab"); saveToRecent("page-skills"); } },
    { id: "page-settings", label: "Settings", icon: "⚙️", category: "page", action: () => { router.push("/settings"); saveToRecent("page-settings"); } },
    
    // Actions
    { id: "action-toggle-sidebar", label: "Toggle Sidebar", icon: "◀", category: "action", action: () => { toggleSidebar(); saveToRecent("action-toggle-sidebar"); } },
    { id: "action-toggle-inspector", label: "Toggle Inspector", icon: "🔍", category: "action", action: () => { toggleInspector(); saveToRecent("action-toggle-inspector"); } },
    
    // Recent agents
    ...agents.slice(0, 3).map((agent) => ({
      id: `agent-${agent.id}`,
      label: `Agent: ${agent.name}`,
      icon: "🤖",
      category: "recent" as const,
      action: () => { router.push(`/agents?id=${agent.id}`); saveToRecent(`agent-${agent.id}`); },
    })),
    
    // Recent missions
    ...missions.slice(0, 3).map((mission) => ({
      id: `mission-${mission.id}`,
      label: `Mission: ${mission.title}`,
      icon: "🎯",
      category: "recent" as const,
      action: () => { router.push(`/missions?id=${mission.id}`); saveToRecent(`mission-${mission.id}`); },
    })),
    
    // Recent goals
    ...goals.slice(0, 3).map((goal) => ({
      id: `goal-${goal.id}`,
      label: `Goal: ${goal.title}`,
      icon: "🏆",
      category: "recent" as const,
      action: () => { router.push(`/goals?id=${goal.id}`); saveToRecent(`goal-${goal.id}`); },
    })),
  ];

  // Filter commands
  const filtered = query
    ? commands.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()))
    : commands;

  // Group by category
  const grouped = filtered.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {} as Record<string, Command[]>);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const execute = useCallback((cmd: Command) => {
    cmd.action();
    setOpen(false);
    setQuery("");
  }, []);

  const handleKey = (e: React.KeyboardEvent) => {
    const items = filtered;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelected((s) => Math.min(s + 1, items.length - 1));
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelected((s) => Math.max(s - 1, 0));
    }
    if (e.key === "Enter" && items[selected]) {
      execute(items[selected]);
    }
  };

  if (!open) return null;

  return (
    <div className="cmd-overlay" onClick={closeCommandPalette}>
      <div className="cmd-modal" onClick={(e) => e.stopPropagation()}>
        <div className="cmd-input-row">
          <span className="cmd-prefix">▶</span>
          <input
            ref={inputRef}
            className="cmd-input"
            placeholder="Rechercher une page, action ou élément..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelected(0);
            }}
            onKeyDown={handleKey}
          />
        </div>
        <div className="cmd-results">
          {Object.entries(grouped).map(([category, cmds]) => {
            const categoryLabel = category === "page" ? "Pages" : category === "action" ? "Actions" : "Récents";
            return (
              <div key={category} className="cmd-group">
                <div className="cmd-group-label">{categoryLabel}</div>
                {cmds.map((cmd, i) => {
                  const globalIndex = filtered.indexOf(cmd);
                  return (
                    <button
                      key={cmd.id}
                      className={`cmd-item ${globalIndex === selected ? "cmd-selected" : ""}`}
                      onClick={() => execute(cmd)}
                      onMouseEnter={() => setSelected(globalIndex)}
                    >
                      <span className="cmd-icon">{cmd.icon}</span>
                      <span className="cmd-label">{cmd.label}</span>
                    </button>
                  );
                })}
              </div>
            );
          })}
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