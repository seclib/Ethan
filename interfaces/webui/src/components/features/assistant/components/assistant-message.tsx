"use client";

import * as React from "react";
import type { AssistantMessage } from "@/types/assistant";
import { ReasoningSection } from "./sections/reasoning-section";
import { ToolsSection } from "./sections/tools-section";
import { DocumentsSection } from "./sections/documents-section";
import { MemorySection } from "./sections/memory-section";
import { MessageFooter } from "./sections/message-footer";
import { MessageActions } from "./message-actions";
import { MarkdownContent } from "./markdown-content";
import { speakText } from "@/lib/api/audio";
import { Volume2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface AssistantMessageProps {
  message: AssistantMessage;
  /** Ce message est-il en cours de génération (curseur animé) ? */
  isStreaming?: boolean;
  onRegenerate?: (assistantMessageId: string) => void;
  /** Édition d'un message utilisateur : renvoi du contenu modifié. */
  onEditMessage?: (messageId: string, newContent: string) => void;
  /** Édition désactivée pendant une génération. */
  editDisabled?: boolean;
}

/** Bouton lecture vocale — synthèse déléguée à ETHAN Core (/v1/audio/synthesize). */
function SpeakButton({ text }: { text: string }) {
  const [speaking, setSpeaking] = React.useState(false);
  return (
    <button
      onClick={async () => {
        if (speaking) return;
        setSpeaking(true);
        try {
          await speakText(text);
        } catch {
          // erreur silencieuse : le pipeline TTS n'est peut-être pas configuré
        } finally {
          setSpeaking(false);
        }
      }}
      className="p-1 rounded hover:bg-bg-1 text-foreground-tertiary opacity-0 group-hover:opacity-100 transition-opacity"
      title="Lire à voix haute"
      aria-label="Lire à voix haute"
    >
      {speaking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Volume2 className="h-4 w-4" />}
    </button>
  );
}

/** Édition inline d'un message utilisateur → renvoi du contenu modifié. */
function UserMessageEditor({
  initial,
  onCancel,
  onSubmit,
}: {
  initial: string;
  onCancel: () => void;
  onSubmit: (content: string) => void;
}) {
  const [value, setValue] = React.useState(initial);
  const ref = React.useRef<HTMLTextAreaElement>(null);

  React.useEffect(() => {
    ref.current?.focus();
    ref.current?.setSelectionRange(value.length, value.length);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="w-full rounded-2xl border border-accent/40 bg-surface-secondary px-3 py-2">
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (value.trim()) onSubmit(value.trim());
          }
          if (e.key === "Escape") onCancel();
        }}
        rows={Math.min(10, value.split("\n").length + 1)}
        className="w-full resize-none bg-transparent text-sm text-foreground focus:outline-none"
      />
      <div className="mt-2 flex items-center justify-end gap-2">
        <span className="mr-auto text-[10px] text-muted-foreground">
          Entrée pour renvoyer · Échap pour annuler
        </span>
        <button
          onClick={onCancel}
          className="rounded-lg px-3 py-1.5 text-xs text-foreground-secondary hover:bg-bg-3"
        >
          Annuler
        </button>
        <button
          onClick={() => value.trim() && onSubmit(value.trim())}
          disabled={!value.trim()}
          className="rounded-lg bg-accent px-3 py-1.5 text-xs text-white hover:bg-accent/90 disabled:opacity-50"
        >
          Renvoyer
        </button>
      </div>
    </div>
  );
}

/**
 * Message renderé selon le visual language Open-WebUI :
 * - Assistant : contenu en ligne (pas de bulle colorée), avatar rond au-dessus
 * - User      : bulle discrète alignée à droite (fond neutre, non accent)
 */
export function AssistantMessageView({
  message,
  isStreaming,
  onRegenerate,
  onEditMessage,
  editDisabled,
}: AssistantMessageProps) {
  const isUser = message.role === "user";
  const [editing, setEditing] = React.useState(false);
  const time = new Date(message.timestamp).toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  // État de génération affiché sous le contenu (stop / erreur).
  const status = message.status;
  const showStoppedNote = status === "stopped";
  const showErrorNote = status === "error";

  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "group relative flex w-full gap-3",
          isUser ? "flex-row-reverse" : "flex-row"
        )}
      >
        {/* Avatar (Claude/ChatGPT style) */}
        {!isUser && (
          <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/10 text-[10px] font-bold text-accent">
            O
          </div>
        )}

        <div
          className={cn(
            "min-w-0 flex-1",
            isUser ? "max-w-[80%]" : "max-w-full"
          )}
        >
          {/* Header */}
          <div className="mb-1 flex items-center gap-2 px-1">
            <span className="text-sm font-medium text-foreground">
              {isUser ? "Vous" : "Odysseus"}
            </span>
            <span className="text-xs text-muted-foreground">{time}</span>
            {!isUser && message.content && <SpeakButton text={message.content} />}
            <MessageActions
              messageId={message.id}
              content={message.content}
              isUser={isUser}
              canRegenerate={!isUser && !!onRegenerate && !editDisabled && status !== "pending"}
              canEdit={isUser && !!onEditMessage && !editDisabled}
              onRegenerate={() => onRegenerate?.(message.id)}
              onEdit={() => setEditing(true)}
            />
          </div>

          {/* Édition inline (messages utilisateur uniquement) */}
          {editing && isUser ? (
            <UserMessageEditor
              initial={message.content}
              onCancel={() => setEditing(false)}
              onSubmit={(content) => {
                setEditing(false);
                onEditMessage?.(message.id, content);
              }}
            />
          ) : (
            /* Contenu — minimaliste : pas de bulle, texte en ligne */
            <div
              className={cn(
                "text-sm leading-relaxed",
                isUser
                  ? "rounded-2xl bg-surface-secondary border border-line-2 px-4 py-2 text-foreground"
                  : "text-foreground"
              )}
            >
              <MarkdownContent content={message.content} />

              {/* Curseur de génération en cours */}
              {isStreaming && (
                <span
                  className="ml-0.5 inline-block h-4 w-[2px] translate-y-[3px] animate-pulse rounded bg-accent"
                  aria-hidden
                />
              )}

              {/* Notes d'état (stop / erreur) */}
              {showStoppedNote && (
                <div className="mt-1 text-xs italic text-muted-foreground">
                  Génération interrompue
                </div>
              )}
              {showErrorNote && (
                <div className="mt-1 text-xs text-red-400">
                  Génération échouée — vérifiez le provider/model puis réessayez.
                </div>
              )}

              {/* Assistant-only sections */}
              {!isUser && (
                <>
                  <ReasoningSection steps={message.reasoning || []} />
                  <DocumentsSection documents={message.documents || []} />
                  <ToolsSection tools={message.tools || []} />
                  <MemorySection entries={message.memoryEntries || []} />
                  <MessageFooter
                    durationMs={message.durationMs}
                    cost={message.cost}
                    tokensUsed={message.tokensUsed}
                    tokensTotal={message.tokensTotal}
                    model={message.model}
                    provider={message.provider}
                  />
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}