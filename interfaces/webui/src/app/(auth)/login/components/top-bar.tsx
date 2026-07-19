"use client";

import { useEffect, useState } from "react";

function formatUTC(date: Date): string {
  return date
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d{3}Z/, " UTC");
}

export function TopBar() {
  const [utcTime, setUtcTime] = useState(formatUTC(new Date()));

  useEffect(() => {
    const interval = setInterval(() => {
      setUtcTime(formatUTC(new Date()));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-10">
      <div className="h-full flex items-center justify-between px-6 border-b border-white/5 bg-[#07090d]/70 backdrop-blur-sm">
        {/* Left: Brand */}
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-semibold tracking-[0.2em] text-cyan-400 uppercase select-none">
            Ethan OS
          </span>
          <span className="w-px h-3 bg-white/10" aria-hidden="true" />
          <span className="text-[10px] tracking-[0.15em] text-white/30 uppercase select-none">
            Classified Access
          </span>
        </div>

        {/* Right: UTC Clock */}
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.5)]" />
          <time
            className="text-[11px] font-mono tracking-[0.1em] text-white/40 select-none"
            dateTime={utcTime}
          >
            {utcTime}
          </time>
        </div>
      </div>
    </header>
  );
}