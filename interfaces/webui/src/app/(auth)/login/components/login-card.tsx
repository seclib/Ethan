"use client";

import { type ReactNode } from "react";
import { motion } from "framer-motion";

interface LoginCardProps {
  children: ReactNode;
}

export function LoginCard({ children }: LoginCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="w-full max-w-[360px]"
    >
      {/* Logo */}
      <div className="mb-10 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full border border-white/10 bg-white/[0.02] mb-4">
          <span className="text-xl font-bold tracking-tight text-cyan-400 select-none">
            E
          </span>
        </div>
        <h1 className="text-xl font-semibold tracking-[0.15em] text-white/90 uppercase select-none">
          ETHAN
        </h1>
        <p className="mt-1 text-[11px] tracking-[0.2em] text-white/30 uppercase font-mono">
          Cognitive Operating System
        </p>
        <div className="mt-4 flex items-center justify-center gap-2">
          <span className="w-4 h-px bg-white/10" />
          <span className="text-[9px] tracking-[0.2em] text-cyan-400/50 uppercase font-mono">
            Secure Authentication Terminal
          </span>
          <span className="w-4 h-px bg-white/10" />
        </div>
      </div>

      {/* Form */}
      <div className="bg-white/[0.02] border border-white/5 rounded-lg p-6">
        {children}
      </div>
    </motion.div>
  );
}