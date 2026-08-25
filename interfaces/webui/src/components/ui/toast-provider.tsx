"use client";

import * as React from "react";
import { useUIStore } from "@/store/ui.store";
import { motion, AnimatePresence } from "framer-motion";
import { Info, CheckCircle2, AlertTriangle, XCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

const toastIcons = {
  info: <Info className="text-accent" size={18} />,
  success: <CheckCircle2 className="text-green-400" size={18} />,
  warning: <AlertTriangle className="text-amber-400" size={18} />,
  error: <XCircle className="text-red-400" size={18} />,
};

const toastStyles = {
  info: "border-accent-line bg-accent-soft",
  success: "border-green-500/20 bg-green-500/10",
  warning: "border-amber-500/20 bg-amber-500/10",
  error: "border-red-500/20 bg-red-500/10",
};

export function ToastProvider() {
  const { toasts, removeToast } = useUIStore();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-3 pointer-events-none w-full max-w-sm">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            layout
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
            className={cn(
              "pointer-events-auto flex items-start gap-3 p-4 rounded-xl border backdrop-blur-md shadow-lg",
              "bg-background/80 border-line-2",
              toastStyles[toast.type]
            )}
          >
            <div className="shrink-0 mt-0.5">{toastIcons[toast.type]}</div>
            
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground leading-tight">
                {toast.message}
              </p>
            </div>
            
            <button
              onClick={() => removeToast(toast.id)}
              className="shrink-0 p-1 rounded-md text-foreground-tertiary hover:text-foreground transition-colors"
            >
              <X size={14} />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
