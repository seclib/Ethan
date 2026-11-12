"use client";

import { CHAT_MODES, type ChatModeValue } from "@/store/chat-mode.store";

interface MessageFooterProps {
  durationMs?: number;
  cost?: number;
  tokensUsed?: number;
  tokensTotal?: number;
  model?: string;
  provider?: string;
  /** Mode conversationnel effectif (plan | act | debug) — badge d'affichage. */
  mode?: string;
}

export function MessageFooter({ durationMs, cost, tokensUsed, tokensTotal, model, provider, mode }: MessageFooterProps) {
  const parts: string[] = [];
  if (durationMs !== undefined) parts.push(`⏱ ${(durationMs / 1000).toFixed(1)}s`);
  if (cost !== undefined) parts.push(`💰 $${cost.toFixed(4)}`);
  if (tokensUsed !== undefined) parts.push(`🔤 ${tokensUsed.toLocaleString()}${tokensTotal ? ` / ${tokensTotal.toLocaleString()}` : ""}`);
  if (model) parts.push(`🤖 ${model}`);
  if (provider) parts.push(`🔌 ${provider}`);

  // Mode résolu par le Core — badge coloré inspiré du sélecteur du composer.
  // Aucun badge pour une valeur inconnue (règle anti-fantôme).
  const modeMeta = mode ? CHAT_MODES[mode as ChatModeValue] : undefined;

  if (parts.length === 0 && !modeMeta) return null;

  return (
    <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
      {modeMeta && (
        <span
          className={`inline-flex items-center gap-1 rounded border border-line-1/60 bg-bg-1 px-1.5 py-0.5 font-medium ${modeMeta.color}`}
          title={modeMeta.description}
        >
          {modeMeta.label}
        </span>
      )}
      {parts.map((part, i) => (
        <span key={i}>{part}</span>
      ))}
    </div>
  );
}
