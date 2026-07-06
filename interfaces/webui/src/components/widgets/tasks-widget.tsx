"use client";

import { useState } from "react";

interface Task {
  id: string;
  label: string;
  done: boolean;
}

interface TasksWidgetProps {
  title?: string;
  tasks: Task[];
  onChange?: (tasks: Task[]) => void;
}

export function TasksWidget({ title = "Tâches", tasks: initial, onChange }: TasksWidgetProps) {
  const [tasks, setTasks] = useState(initial);
  const [input, setInput] = useState("");

  const toggle = (id: string) => {
    const next = tasks.map((t) => (t.id === id ? { ...t, done: !t.done } : t));
    setTasks(next);
    onChange?.(next);
  };

  const add = () => {
    if (!input.trim()) return;
    const next = [...tasks, { id: crypto.randomUUID(), label: input.trim(), done: false }];
    setTasks(next);
    onChange?.(next);
    setInput("");
  };

  return (
    <div className="tasks-widget">
      <div className="tasks-header">{title}</div>
      <div className="tasks-list">
        {tasks.map((t) => (
          <label key={t.id} className="tasks-item" data-done={t.done}>
            <input
              type="checkbox"
              checked={t.done}
              onChange={() => toggle(t.id)}
              className="tasks-checkbox"
            />
            <span className="tasks-label">{t.label}</span>
          </label>
        ))}
      </div>
      <div className="tasks-add">
        <input
          className="tasks-input"
          placeholder="Ajouter une tâche..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
        />
        <button className="tasks-add-btn" onClick={add}>+</button>
      </div>
    </div>
  );
}