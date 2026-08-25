"use client";

import * as React from "react";
import { Copy, Check, RefreshCw, Pencil } from "lucide-react";
import { useUIStore } from "@/store/ui.store";

interface MessageActionsProps {
  messageId: string;
  content: string;
  isUser: boolean;
  /** Régénération disponible (dernière réponse, génération terminée). */
  canRegenerate?: boolean;
  /** Édition disponible (messages utilisateur). */
  canEdit?: boolean;
  onRegenerate?: () => void;
  onEdit?: () => void;
}

/**
 * Actions par message — toutes fonctionnelles :
 * - Copier     : presse-papiers + feedback visuel ✓
 * - Régénérer  : renvoi du dernier message utilisateur (nouvelle branche Core)
 * - Éditer     : édition inline + renvoi du contenu modifié
 */
export function MessageActions({
  content,
  canRegenerate,
  canEdit,
  onRegenerate,
  onEdit,
}: MessageActionsProps) {
  const [copied, setCopied] = React.useState(false);
  const addToast = useUIStore((s) => s.addToast);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      addToast({ type: "error", message: "Copie impossible (presse-papiers indisponible)" });
    }
  };

  return (
    <div className="flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
      <button
        onClick={handleCopy}
        className="rounded p-1 text-foreground-tertiary hover:bg-bg-1 hover:text-foreground"
        title="Copier"
        aria-label="Copier le message"
      >
        {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
      </button>

      {canRegenerate && (
        <button
          onClick={onRegenerate}
          className="rounded p-1 text-foreground-tertiary hover:bg-bg-1 hover:text-foreground"
          title="Régénérer la réponse"
          aria-label="Régénérer la réponse"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      )}

      {canEdit && (
        <button
          onClick={onEdit}
          className="rounded p-1 text-foreground-tertiary hover:bg-bg-1 hover:text-foreground"
          title="Modifier et renvoyer"
          aria-label="Modifier le message"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}