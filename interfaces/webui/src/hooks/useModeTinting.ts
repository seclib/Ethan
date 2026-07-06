"use client";

import { useEffect } from "react";

const MODES = {
  home: { chapter: "—", num: "00", label: "ETHAN", watermark: "" },
  dashboard: { chapter: "I", num: "01", label: "DASHBOARD", watermark: "Dashboard" },
  chat: { chapter: "II", num: "02", label: "CHAT", watermark: "Chat" },
  settings: { chapter: "III", num: "03", label: "RÉGLAGES", watermark: "Réglages" },
};

export function useModeTinting(mode: keyof typeof MODES) {
  useEffect(() => {
    const body = document.body;
    const meta = MODES[mode] || MODES.home;

    body.dataset.mode = mode;

    // Watermark
    let wm = document.getElementById("j-watermark");
    if (meta.watermark) {
      if (!wm) {
        wm = document.createElement("div");
        wm.id = "j-watermark";
        wm.className = "mode-watermark";
        document.body.appendChild(wm);
      }
      wm.textContent = meta.watermark;
    } else if (wm) {
      wm.textContent = "";
    }

    // Chapter indicator
    const ch = document.getElementById("j-rooms-chapter");
    if (ch && meta.chapter !== "—") {
      const numEl = ch.querySelector(".rooms-num");
      const lblEl = ch.querySelector(".rooms-lbl");
      if (numEl) numEl.textContent = meta.chapter;
      if (lblEl) lblEl.textContent = meta.label;
    }
  }, [mode]);
}