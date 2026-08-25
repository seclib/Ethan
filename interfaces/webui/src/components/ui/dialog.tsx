"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

interface DialogContextType {
  open: boolean;
  onClose: () => void;
}

const DialogContext = React.createContext<DialogContextType | undefined>(undefined);

function useDialog() {
  const context = React.useContext(DialogContext);
  if (!context) {
    throw new Error("Dialog sub-components must be used within a Dialog");
  }
  return context;
}

export interface DialogProps {
  open: boolean;
  onClose?: () => void;
  onOpenChange?: (open: boolean) => void;
  size?: "sm" | "md" | "lg" | "xl";
  title?: string;
  children: React.ReactNode;
}

function Dialog({ open, onClose, onOpenChange, size = "md", title, children }: DialogProps) {
  const handleClose = React.useCallback(() => {
    onClose?.();
    onOpenChange?.(false);
  }, [onClose, onOpenChange]);

    // Save & restore focus on open/close for keyboard accessibility
  const previouslyFocusedRef = React.useRef<HTMLElement | null>(null);
  const dialogRef = React.useRef<HTMLDivElement>(null);

  // Focus trap + Escape + tab cycling (a11y)
  React.useEffect(() => {
    if (!open) {
      previouslyFocusedRef.current?.focus?.();
      previouslyFocusedRef.current = null;
      return;
    }

    previouslyFocusedRef.current = document.activeElement as HTMLElement | null;
    // Focus the dialog panel itself
    dialogRef.current?.focus();

    const focusableSelectors = [
      "button",
      "input",
      "textarea",
      "select",
      "[tabindex]:not([tabindex='-1'])",
    ].join(",");

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        handleClose();
        return;
      }

      // Tab key focus trap
      if (e.key === "Tab" && dialogRef.current) {
        const focusableEls: HTMLElement[] = Array.from(
          dialogRef.current.querySelectorAll<HTMLElement>(focusableSelectors),
        ).filter((el) => el.offsetWidth > 0 || el.offsetHeight > 0 || el === document.activeElement);

        if (focusableEls.length === 0) return;

        const firstEl = focusableEls[0];
        const lastEl = focusableEls[focusableEls.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstEl) {
            e.preventDefault();
            lastEl.focus();
          }
        } else {
          if (document.activeElement === lastEl) {
            e.preventDefault();
            firstEl.focus();
          }
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, handleClose]);

  if (!open) return null;

  const sizeClasses = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
  };

  return (
    <DialogContext.Provider value={{ open, onClose: handleClose }}>
      <div
        className="fixed inset-0 z-modal flex items-center justify-center"
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "dialog-title" : undefined}
      >
        {/* Backdrop */}
        <div
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={handleClose}
          aria-hidden="true"
        />

                {/* Panel — style Odysseus (.modal-content) */}
        <div
          ref={dialogRef}
          tabIndex={-1}
          className={cn(
            "modal-content relative w-full mx-4",
            "animate-in fade-in zoom-in-95 duration-200",
            sizeClasses[size]
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-line-1">
            <h2
              id="dialog-title"
              className="text-base font-semibold text-foreground"
            >
              {title || "Dialog"}
            </h2>
            <button
              onClick={handleClose}
              className="text-foreground-tertiary hover:text-foreground transition-colors duration-100"
              aria-label="Close dialog"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-4">{children}</div>
        </div>
      </div>
    </DialogContext.Provider>
  );
}

export { Dialog };