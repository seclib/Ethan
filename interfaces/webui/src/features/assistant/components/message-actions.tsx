"use client";

import * as React from "react";

interface MessageActionsProps {
  messageId: string;
  content: string;
  isUser: boolean;
  onCopy?: () => void;
  onRegenerate?: () => void;
  onDelete?: () => void;
}

export function MessageActions({
  messageId,
  content,
  isUser,
  onCopy,
  onRegenerate,
  onDelete,
}: MessageActionsProps) {
  const [showMenu, setShowMenu] = React.useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    onCopy?.();
    setShowMenu(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="p-1 rounded hover:bg-bg-1 text-foreground-tertiary opacity-0 group-hover:opacity-100 transition-opacity"
        title="Actions"
      >
        <svg
          className="h-4 w-4"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
        </svg>
      </button>

      {showMenu && (
        <div className="absolute right-0 mt-1 w-32 rounded-md border border-line-1 bg-bg-2 shadow-lg z-10">
          <button
            onClick={handleCopy}
            className="w-full text-left px-3 py-1.5 text-sm text-foreground hover:bg-bg-3"
          >
            📋 Copier
          </button>
          {!isUser && onRegenerate && (
            <button
              onClick={() => {
                onRegenerate();
                setShowMenu(false);
              }}
              className="w-full text-left px-3 py-1.5 text-sm text-foreground hover:bg-bg-3"
            >
              🔄 Régénérer
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => {
                onDelete();
                setShowMenu(false);
              }}
              className="w-full text-left px-3 py-1.5 text-sm text-red-400 hover:bg-bg-3"
            >
              🗑 Supprimer
            </button>
          )}
        </div>
      )}
    </div>
  );
}