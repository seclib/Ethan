"use client";

import { useStore } from "@/lib/store";

export function Inspector() {
  const { inspector, closeInspector } = useStore();

  if (!inspector.open) return null;

  return (
    <aside className="inspector">
      <div className="inspector-header">
        <span className="inspector-title">
          {inspector.type ? inspector.type.charAt(0).toUpperCase() + inspector.type.slice(1) : "Details"}
        </span>
        <button className="inspector-close" onClick={closeInspector}>✕</button>
      </div>
      <div className="inspector-body">
        <div className="inspector-field">
          <span className="inspector-field-label">ID</span>
          <span className="inspector-field-value">{inspector.id}</span>
        </div>
        {inspector.data !== null && typeof inspector.data === "object" && (
          <>
            {Object.entries(inspector.data as Record<string, unknown>).map(([key, val]) => (
              <div key={key} className="inspector-field">
                <span className="inspector-field-label">{key}</span>
                <span className="inspector-field-value">
                  {typeof val === "object" ? JSON.stringify(val, null, 2) : String(val as string)}
                </span>
              </div>
            ))}
          </>
        )}
      </div>
    </aside>
  );
}