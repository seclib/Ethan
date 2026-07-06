"use client";

import { useEffect } from "react";

export function MissionControlTrigger() {
  useEffect(() => {
    const btn = document.createElement("button");
    btn.id = "j-rooms-mc";
    btn.className = "rooms-mc";
    btn.innerHTML = `
      <span class="mc-dot"></span>
      <span>Mission Control</span>
      <span class="mc-kbd"><span>⌘</span><span>T</span></span>
    `;
    btn.addEventListener("click", () => {
      console.log("Mission Control (⌘T)");
    });
    document.body.appendChild(btn);
    return () => { btn.remove(); };
  }, []);
  return null;
}