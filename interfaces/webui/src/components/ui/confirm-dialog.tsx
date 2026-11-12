"use client";

/**
 * ETHAN WebUI — ConfirmDialog (pattern Open-WebUI « ConfirmDialog.svelte »).
 *
 * Remplace les window.confirm() natifs : dialog cohérent avec le thème,
 * focus trap/Escape hérités du Dialog, Enter = confirmer, Esc = annuler.
 * Usage contrôlé : <ConfirmDialog open={..} onOpenChange={..} onConfirm={..} />
 */

import * as React from "react";
import { Dialog } from "./dialog";
import { Button } from "./button";

export interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  /** Corps du dialog (texte simple). */
  message?: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Style destructif (rouge) pour les suppressions. */
  destructive?: boolean;
  onConfirm: () => void;
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  message,
  confirmLabel = "Confirmer",
  cancelLabel = "Annuler",
  destructive = false,
  onConfirm,
}: ConfirmDialogProps) {
  const handleConfirm = () => {
    onOpenChange(false);
    onConfirm();
  };

  // Enter = confirmer (pattern Open-WebUI), Esc géré par le Dialog.
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleConfirm();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange} size="sm" title={title}>
      <div onKeyDown={handleKeyDown}>
        {message && (
          <p className="text-sm leading-relaxed text-foreground-secondary">{message}</p>
        )}
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {cancelLabel}
          </Button>
          <Button
            variant={destructive ? "destructive" : "default"}
            onClick={handleConfirm}
            autoFocus
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
