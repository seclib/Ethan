"use client";

import { useEffect } from "react";

export function useAtmosphere() {
  useEffect(() => {
    const body = document.body;

    // Spotlight (suit la souris)
    let spotlight = document.getElementById("j-spotlight");
    if (!spotlight) {
      spotlight = document.createElement("div");
      spotlight.id = "j-spotlight";
      spotlight.className = "spotlight";
      body.appendChild(spotlight);
    }

    const onMouseMove = (e: MouseEvent) => {
      if (spotlight) {
        spotlight.style.setProperty("--mx", e.clientX + "px");
        spotlight.style.setProperty("--my", e.clientY + "px");
      }
    };
    window.addEventListener("mousemove", onMouseMove, { passive: true });

    // Atmosphere layers
    if (!document.querySelector(".atmo--vignette")) {
      body.appendChild(document.createElement("div")).className = "atmo atmo--aurora";
      body.appendChild(document.createElement("div")).className = "atmo atmo--vignette";
      body.appendChild(document.createElement("div")).className = "atmo atmo--grain";
      body.appendChild(document.createElement("div")).className = "mode-glow";
    }

    return () => {
      window.removeEventListener("mousemove", onMouseMove);
    };
  }, []);
}