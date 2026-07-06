"use client";

import { useEffect } from "react";

export function ChapterIndicator() {
  useEffect(() => {
    const ch = document.createElement("div");
    ch.id = "j-rooms-chapter";
    ch.className = "rooms-chapter";
    ch.innerHTML = `
      <span class="rooms-num">—</span>
      <span class="rooms-bar"></span>
      <span class="rooms-lbl">ETHAN</span>
    `;
    document.body.appendChild(ch);
    return () => { ch.remove(); };
  }, []);
  return null;
}
