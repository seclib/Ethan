"use client";

interface TypingIndicatorProps {
  className?: string;
}

/**
 * Indicateur de frappe animé inspiré d'Open-WebUI.
 * Affiche 3 points animés pour indiquer que l'assistant est en train de répondre.
 */
export function TypingIndicator({ className = "" }: TypingIndicatorProps) {
  return (
    <div className={`flex justify-start ${className}`}>
      <div className="max-w-[85%]">
        {/* Header */}
        <div className="flex items-center gap-2 mb-1 px-1">
          <span className="text-xs font-medium text-purple-400">Assistant</span>
        </div>

        {/* Bubble with typing animation */}
        <div className="rounded-lg px-4 py-3 bg-background/40 border border-line-1/20">
          <div className="flex items-center gap-1">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-foreground-tertiary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-foreground-tertiary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-foreground-tertiary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}