"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const ROOMS = [
  { id: "home", label: "Home", desc: "Écran ambiant", icon: "⌂", mode: "home" },
  { id: "dashboard", label: "Dashboard", desc: "Pilotage & KPI", icon: "◉", mode: "workspace" },
  { id: "chat", label: "Chat", desc: "Conversation IA", icon: "💬", mode: "chat" },
  { id: "settings", label: "Settings", desc: "Configuration", icon: "⚙", mode: "config" },
];

export function MissionControl() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "t") {
        e.preventDefault();
        setOpen((v: boolean) => !v);
      }
      if (e.key === "Escape" && open) {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const close = () => setOpen(false);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="mission-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div className="mc-header">
            <span className="mc-header-title">Mission Control</span>
            <span className="mc-header-hint">
              <span className="mc-hkbd"><span>ESC</span></span> pour fermer
            </span>
            <button className="mc-close" onClick={close}>✕</button>
          </div>
          <div className="mission-grid">
            {ROOMS.map((room) => (
              <motion.button
                key={room.id}
                className="mission-card"
                data-mode={room.mode}
                whileHover={{ scale: 1.01 }}
                onClick={() => {
                  window.location.href = `/${room.id === 'home' ? '' : room.id}`;
                  close();
                }}
              >
                <div className="mc-card-eyebrow">
                  <span className="mc-card-num">0{ROOMS.indexOf(room) + 1}</span>
                  <span>{room.icon}</span>
                </div>
                <div className="mc-card-title">{room.label}</div>
                <div className="mc-card-desc">{room.desc}</div>
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}