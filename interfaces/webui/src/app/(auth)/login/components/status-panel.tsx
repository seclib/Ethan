"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface StatusItem {
  label: string;
  value: string;
  dot: "cyan" | "green" | "amber" | "red";
}

const STATUS_ITEMS: StatusItem[] = [
  { label: "NETWORK", value: "ONLINE", dot: "cyan" },
  { label: "AI CORE", value: "READY", dot: "green" },
  { label: "PLUGIN ENGINE", value: "ONLINE", dot: "cyan" },
  { label: "MEMORY", value: "SYNCED", dot: "green" },
  { label: "VECTOR DATABASE", value: "CONNECTED", dot: "green" },
  { label: "GPU", value: "AVAILABLE", dot: "cyan" },
  { label: "SECURITY LEVEL", value: "OMEGA", dot: "amber" },
];

const DOT_COLORS: Record<string, string> = {
  cyan: "bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.5)]",
  green: "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]",
  amber: "bg-amber-400 shadow-[0_0_6px_rgba(245,158,11,0.5)]",
  red: "bg-red-400 shadow-[0_0_6px_rgba(239,68,68,0.5)]",
};

function formatUTC(date: Date): string {
  return date
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d{3}Z/, " UTC");
}

function StatusRow({ item, index }: { item: StatusItem; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.4 + index * 0.06, duration: 0.4, ease: "easeOut" }}
      className="flex items-center justify-between py-1.5"
    >
      <span className="text-[10px] tracking-[0.15em] text-white/30 uppercase font-mono">
        {item.label}
      </span>
      <div className="flex items-center gap-2">
        <span className="text-[10px] tracking-[0.1em] text-white/50 font-mono">
          {item.value}
        </span>
        <span
          className={`w-1.5 h-1.5 rounded-full ${DOT_COLORS[item.dot]}`}
        />
      </div>
    </motion.div>
  );
}

export function StatusPanel() {
  const [utcTime, setUtcTime] = useState(formatUTC(new Date()));

  useEffect(() => {
    const interval = setInterval(() => {
      setUtcTime(formatUTC(new Date()));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.aside
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="hidden lg:flex flex-col w-[240px] border-l border-white/5 bg-white/[0.015]"
    >
      <div className="flex-1 flex flex-col justify-center px-6 py-12">
        {/* Status items */}
        <div className="space-y-0.5">
          {STATUS_ITEMS.map((item, i) => (
            <StatusRow key={item.label} item={item} index={i} />
          ))}
        </div>

        {/* Separator */}
        <div className="my-6 border-t border-white/5" />

        {/* System clock */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.0, duration: 0.4 }}
        >
          <div className="flex items-center justify-between py-1.5">
            <span className="text-[10px] tracking-[0.15em] text-white/30 uppercase font-mono">
              SYSTEM CLOCK
            </span>
            <time
              className="text-[10px] font-mono tracking-[0.1em] text-white/40"
              dateTime={utcTime}
            >
              {utcTime}
            </time>
          </div>
        </motion.div>

        {/* Active session */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.1, duration: 0.4 }}
        >
          <div className="flex items-center justify-between py-1.5">
            <span className="text-[10px] tracking-[0.15em] text-white/30 uppercase font-mono">
              ACTIVE SESSION
            </span>
            <span className="text-[10px] font-mono tracking-[0.1em] text-white/40">
              NONE
            </span>
          </div>
        </motion.div>

        {/* Version */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.4 }}
        >
          <div className="flex items-center justify-between py-1.5">
            <span className="text-[10px] tracking-[0.15em] text-white/30 uppercase font-mono">
              VERSION
            </span>
            <span className="text-[10px] font-mono tracking-[0.1em] text-white/40">
              2.4.1
            </span>
          </div>
        </motion.div>
      </div>
    </motion.aside>
  );
}