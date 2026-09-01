"use client";

import * as React from "react";
import { useUIStore } from "@/store/ui.store";
import { motion, AnimatePresence } from "framer-motion";
import { Info, CheckCircle2, AlertTriangle, XCircle, X } from "lucide-react";

const toastIcons = {
  info: <Info size={14} />,
  success: <CheckCircle2 size={14} />,
  warning: <AlertTriangle size={14} />,
  error: <XCircle size={14} />,
};

/* Toast style : dark panel, 3px colored left border,
   12px text. Colors via theme tokens (--accent,
   --green, --amber/--gold, --red) to follow the active theme. */
const toastAccent: Record<string, { borderLeft: string; iconColor: string }> = {
  info: { borderLeft: "var(--accent)", iconColor: "var(--accent)" },
  success: { borderLeft: "var(--green)", iconColor: "var(--green)" },
  warning: { borderLeft: "var(--gold)", iconColor: "var(--gold)" },
  error: { borderLeft: "var(--red)", iconColor: "var(--red)" },
};

export function ToastProvider() {
  const { toasts, removeToast } = useUIStore();

  return (
    <div className="fixed right-4 top-4 z-toast flex w-full max-w-[360px] flex-col gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => {
          const accent = toastAccent[toast.type] ?? toastAccent.info;
          return (
            <motion.div
              key={toast.id}
              layout
              initial={{ opacity: 0, x: "120%" }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: "-120%", transition: { duration: 0.35 } }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              role="status"
              aria-live="polite"
              className="pointer-events-auto flex min-h-[34px] max-w-[360px] items-center gap-2 rounded-md py-2 pl-3 pr-2 text-xs backdrop-blur-md"
              style={{
                background: "color-mix(in srgb, var(--panel) 88%, transparent)",
                color: "var(--fg)",
                border: `1px solid color-mix(in srgb, ${accent.borderLeft} 30%, transparent)`,
                borderLeft: `3px solid ${accent.borderLeft}`,
                boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
              }}
            >
              <span className="shrink-0" style={{ color: accent.iconColor }}>
                {toastIcons[toast.type]}
              </span>

              <p className="min-w-0 flex-1 leading-snug">{toast.message}</p>

              <button
                onClick={() => removeToast(toast.id)}
                className="shrink-0 rounded p-0.5 opacity-50 transition-opacity hover:opacity-100"
                aria-label="Fermer"
              >
                <X size={12} />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
