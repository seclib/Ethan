"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui.store";

function Toast({ id, type, message, duration = 5000 }: {
  id: string;
  type: "info" | "success" | "warning" | "error";
  message: string;
  duration?: number;
}) {
  const removeToast = useUIStore((state) => state.removeToast);

  React.useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        removeToast(id);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [id, duration, removeToast]);

  const icons = {
    info: "ℹ",
    success: "✓",
    warning: "⚠",
    error: "✗",
  };

  const colors = {
    info: "border-accent text-accent",
    success: "border-green-500 text-green-400",
    warning: "border-amber-500 text-amber-400",
    error: "border-red-500 text-red-400",
  };

  return (
    <div
      className={cn(
        "toast flex items-center gap-3 p-4 rounded-lg border bg-background shadow-lg",
        "animate-in slide-in-from-top-2 duration-300",
        colors[type]
      )}
    >
      <span className="text-lg">{icons[type]}</span>
      <p className="flex-1 text-sm">{message}</p>
      <button
        onClick={() => removeToast(id)}
        className="text-muted-foreground hover:text-foreground transition-colors"
      >
        ✕
      </button>
    </div>
  );
}

function ToastContainer() {
  const toasts = useUIStore((state) => state.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} />
      ))}
    </div>
  );
}

export { Toast, ToastContainer };