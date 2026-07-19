"use client";

interface MessageFooterProps {
  durationMs?: number;
  cost?: number;
  tokensUsed?: number;
  tokensTotal?: number;
  model?: string;
  provider?: string;
}

export function MessageFooter({ durationMs, cost, tokensUsed, tokensTotal, model, provider }: MessageFooterProps) {
  const parts: string[] = [];
  if (durationMs !== undefined) parts.push(`⏱ ${(durationMs / 1000).toFixed(1)}s`);
  if (cost !== undefined) parts.push(`💰 $${cost.toFixed(4)}`);
  if (tokensUsed !== undefined) parts.push(`🔤 ${tokensUsed.toLocaleString()}${tokensTotal ? ` / ${tokensTotal.toLocaleString()}` : ""}`);
  if (model) parts.push(`🤖 ${model}`);
  if (provider) parts.push(`🔌 ${provider}`);

  if (parts.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-500">
      {parts.map((part, i) => (
        <span key={i}>{part}</span>
      ))}
    </div>
  );
}