"use client";

import { useEffect, useState } from "react";
import { useTheme } from "@/core/providers/theme-provider";

export function AtmosphereLayer() {
  const { resolvedTheme } = useTheme();
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });

  useEffect(() => {
    if (resolvedTheme !== "dark") return;

    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth) * 100;
      const y = (e.clientY / window.innerHeight) * 100;
      setMousePos({ x, y });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [resolvedTheme]);

  if (resolvedTheme !== "dark") return null;

  return (
    <>
      <div className="atmo atmo--vignette" />
      <div className="atmo atmo--grain" />
      <div className="atmo atmo--aurora" />
      <div 
        className="spotlight" 
        style={{ 
          background: `radial-gradient(360px at ${mousePos.x}% ${mousePos.y}%, rgba(96, 165, 250, 0.04), transparent 70%)` 
        }} 
      />
      <div className="mode-glow" />
    </>
  );
}
