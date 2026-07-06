"use client";

import { useEffect, useRef } from "react";
import { useStore, type AppPage, PAGE_TITLES } from "@/lib/store";

export function ContextMenu() {
  const { contextMenu, closeContextMenu, setPage } = useStore();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!contextMenu.open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        closeContextMenu();
      }
    }
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") closeContextMenu();
    }
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [contextMenu.open, closeContextMenu]);

  if (!contextMenu.open || !contextMenu.page) return null;

  const page = contextMenu.page;

  return (
    <div
      ref={ref}
      className="ctx-menu"
      style={{ left: contextMenu.x, top: contextMenu.y }}
    >
      <button className="ctx-item" onClick={() => { setPage(page); closeContextMenu(); }}>
        <span className="ctx-icon">→</span> Ouvrir
      </button>
      <button className="ctx-item" onClick={() => { window.open(window.location.href, "_blank"); closeContextMenu(); }}>
        <span className="ctx-icon">⊕</span> Ouvrir dans un nouvel onglet
      </button>
      <div className="ctx-sep" />
      <button className="ctx-item" onClick={() => { navigator.clipboard.writeText(page); closeContextMenu(); }}>
        <span className="ctx-icon">📋</span> Copier l'ID
      </button>
      <button className="ctx-item" onClick={() => { navigator.clipboard.writeText(PAGE_TITLES[page]); closeContextMenu(); }}>
        <span className="ctx-icon">📄</span> Copier le nom
      </button>
      <div className="ctx-sep" />
      <button className="ctx-item ctx-disabled" disabled>
        <span className="ctx-icon">?</span> Aide : {PAGE_TITLES[page]}
      </button>
    </div>
  );
}