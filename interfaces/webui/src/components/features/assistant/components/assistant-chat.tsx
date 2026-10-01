"use client";

import { useState, useRef, useEffect, useCallback, type ReactNode } from "react";
import { ArrowDown, AlertCircle, X, Loader2 } from "lucide-react";
import type { AssistantMessage, SessionMetrics } from "@/types/assistant";
import { AssistantMessageView } from "./assistant-message";
import { AssistantInput } from "./assistant-input";
export { AssistantInput } from "./assistant-input";
import { TypingIndicator } from "./typing-indicator";
import { ChatGreeting } from "./chat-greeting";

/** Item de sélection d'une capacité dans le composer. */
export interface ComposerCapabilityItem {
  id: string;
  name: string;
  /** Badge optionnel (ex. provider d'un tool : builtin / mcp). */
  badge?: string;
}

interface AssistantChatProps {
  messages: AssistantMessage[];
  /**
   * Métriques de session — rendues par la ChatSecondaryBar (header). Optionnel :
   * le corps du Chat ne les affiche pas ; conservé pour compatibilité appelants.
   */
  metrics?: SessionMetrics;
  /** Identifiant de la conversation courante — déclenche le retour en bas au changement. */
  chatId?: string | null;
  /** Chargement d'un historique en cours. */
  isLoading?: boolean;
  /**
   * Conversation vierge : bloc hero NON extensible (salutation + composer),
   * centré verticalement par la page. Ignoré si la conversation contient des
   * messages ou si un historique est en cours de chargement (sécurité).
   */
  hero?: boolean;
  /**
   * Invite contextuelle de la section active (ChatGreeting) — présentation pure.
   * La section appartient au store UI ; le Core reste seul arbitre des
   * capacités réellement envoyées dans le payload chat.
   */
  sectionHint?: string;
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  /** File attachment handler (legacy : ouverture déléguée à la page). */
  onAttach?: () => void;
  /**
   * Fichiers choisis dans le picker natif. L'UPLOAD appartient à la page
   * propriétaire (Core : POST /files/upload) ; le chat ne fait que relayer.
   */
  onFilesSelected?: (files: File[]) => void;
  /** Fichiers joints (état possédé par la page) — rendus dans le composer. */
  attachedFiles?: { id: string; name: string }[];
  /** Retrait d'un fichier joint (état possédé par la page). */
  onRemoveFile?: (id: string) => void;
  /** Search toggle handler. */
  onSearch?: () => void;
  /** Tools toggle handler. */
  onTools?: () => void;
  /** Voice input handler. */
  onVoice?: () => void;
  /**
   * Slot Plugins (picker compact rendu dans les contrôles du composer).
   * Voir AssistantInput.pluginsSlot — la page propriétaire fournit le
   * composant complet (catalogue Core + sélection conversation).
   */
  pluginsSlot?: ReactNode;
  /**
   * Slot Mode (ChatModeToggle) — rendu dans la rangée de contrôles du bas du
   * composer, à côté de l'import de fichiers. Possédé par la page via le
   * store chat-mode ; le Core, seul, arbitre la capacité (modes.py).
   */
  modeSlot?: ReactNode;
  /**
   * NOTE (dé-duplication) : les props capacités du composer (skills/collections/
   * tools/sélections/provider/model) ont été RETIRÉES — le composer simplifié
   * ne les rend plus. Les sélections actives vivent dans la page (payload chat)
   * et leur représentation visuelle est la ChatContextBar ; les sélecteurs
   * Agent/Model ont UNE position : le header (ChatSecondaryBar).
   */
  /** Erreur globale du flux (use-chats) — affichée en bannière non bloquante. */
  error?: string | null;
  onDismissError?: () => void;
  /** Régénère la réponse qui suit le dernier message utilisateur. */
  onRegenerate?: (assistantMessageId: string) => void;
  /** Édition d'un message utilisateur : renvoi du contenu modifié. */
  onEditMessage?: (messageId: string, newContent: string) => void;
}

/** Seuil (px) sous lequel on considère l'utilisateur « en bas » du fil. */
const BOTTOM_THRESHOLD = 80;

export function AssistantChat({
  messages,
  metrics,
  chatId,
  isLoading,
  hero,
  sectionHint,
  onSend,
  onStop,
  disabled,
  onAttach,
  onFilesSelected,
  attachedFiles,
  onRemoveFile,
  onSearch,
  onTools,
  onVoice,
  pluginsSlot,
  modeSlot,
  error,
  onDismissError,
  onRegenerate,
  onEditMessage,
}: AssistantChatProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  // Ref (et non state) : lu dans les effets sans recréer de closures obsolètes.
  const autoScrollRef = useRef(true);
  const [showScrollDown, setShowScrollDown] = useState(false);

  /** L'utilisateur est-il en bas du fil ? */
  const isNearBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_THRESHOLD;
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior });
  }, []);

  /** Scroll utilisateur : s'il remonte, on coupe l'auto-scroll. */
  const handleScroll = useCallback(() => {
    const nearBottom = isNearBottom();
    autoScrollRef.current = nearBottom;
    setShowScrollDown(!nearBottom);
  }, [isNearBottom]);

  /**
   * Changement de conversation (ouverture historique, refresh, nouvelle
   * conversation) : retour en bas immédiat et réactivation de l'auto-scroll.
   */
  useEffect(() => {
    autoScrollRef.current = true;
    setShowScrollDown(false);
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [chatId]);

  /**
   * Auto-scroll pendant la génération — uniquement si l'utilisateur
   * n'a pas remonté le fil. Double requestAnimationFrame : attend que le
   * markdown soit peint avant de mesurer scrollHeight (messages longs).
   */
  useEffect(() => {
    if (!autoScrollRef.current) return;
    let frame2 = 0;
    const frame1 = requestAnimationFrame(() => {
      frame2 = requestAnimationFrame(() =>
        scrollToBottom(disabled ? "auto" : "smooth"),
      );
    });
    return () => {
      cancelAnimationFrame(frame1);
      cancelAnimationFrame(frame2);
    };
  }, [messages, disabled, scrollToBottom]);

  // Dernier message assistant = celui en cours de génération pendant `disabled`.
  const lastAssistantId = [...messages].reverse().find((m) => m.role === "assistant")?.id;
  /**
   * En attente du premier token : génération active mais la réponse assistant
   * n'affiche encore aucun contenu — c'est le seul cas où l'indicateur de
   * frappe est affiché (sinon il ferait doublon avec le texte qui stream).
   */
  const lastAssistant = messages.find((m) => m.id === lastAssistantId);
  const waitingForFirstToken =
    !!disabled && (!lastAssistant || (!lastAssistant.content && !lastAssistant.done));

  /**
   * État vide (hero) : la page centre verticalement le bloc [salutation,
   * composer, sections]. Le hero n'est honoré QUE pour une conversation
   * réellement vierge — jamais pendant un chargement d'historique.
   */
  const showHero = !!hero && messages.length === 0 && !isLoading;

  /** Bannière d'erreur — non bloquante, partagée par les deux dispositions. */
  const errorBanner = error ? (
    <div className="mx-auto mb-1 flex w-full max-w-3xl items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
      <AlertCircle size={15} className="mt-0.5 shrink-0" />
      <span className="min-w-0 flex-1 break-words">{error}</span>
      {onDismissError && (
        <button
          onClick={onDismissError}
          className="shrink-0 rounded p-0.5 text-red-400/70 hover:bg-red-500/10 hover:text-red-400"
          title="Fermer"
          aria-label="Fermer l'erreur"
        >
          <X size={14} />
        </button>
      )}
    </div>
  ) : null;

  /**
   * Composer — MÊME élément dans les deux dispositions (source unique) :
   * fichiers joints et slots appartiennent à la page ; l'input les rend à leur
   * place et remonte les actions, sans logique métier propre.
   */
  const composer = (
    <AssistantInput
      onSend={onSend}
      onStop={onStop}
      disabled={disabled}
      onAttach={onAttach}
      onFilesSelected={onFilesSelected}
      attachedFiles={attachedFiles}
      onRemoveFile={onRemoveFile}
      onSearch={onSearch}
      onTools={onTools}
      onVoice={onVoice}
      pluginsSlot={pluginsSlot}
      modeSlot={modeSlot}
    />
  );

  if (showHero) {
    return (
      <div className="flex w-full flex-col gap-5">
        <ChatGreeting hint={sectionHint} />
        {errorBanner}
        {composer}
      </div>
    );
  }

  return (
    <div className="relative flex-1 flex flex-col min-h-0">
      {/* Messages — wrapper relatif : le bouton « retour en bas » s'ancre à la
          SEULE zone des messages (et non au conteneur chat complet). Sinon son
          offset `bottom` fixe entre en collision avec le composer quand la
          textarea grandit (auto-resize jusqu'à 200px). */}
      <div className="relative flex-1 min-h-0">
        <div ref={scrollRef} onScroll={handleScroll} className="h-full overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6 space-y-6">
          {isLoading && (
            <div className="flex justify-center py-6" role="status" aria-label="Chargement de la conversation">
              <Loader2 size={20} className="animate-spin text-muted-foreground" />
            </div>
          )}
          {messages.map((msg) => (
            <AssistantMessageView
              key={msg.id}
              message={msg}
              isStreaming={disabled && msg.id === lastAssistantId && !msg.done}
              onRegenerate={onRegenerate}
              onEditMessage={onEditMessage}
              editDisabled={disabled}
            />
          ))}
          {waitingForFirstToken && <TypingIndicator />}
          <div className="h-1" />
        </div>
        </div>

        {/* Bouton retour en bas — visible dès que l'utilisateur a remonté le fil */}
        {showScrollDown && (
          <button
            onClick={() => {
              autoScrollRef.current = true;
              setShowScrollDown(false);
              scrollToBottom("smooth");
            }}
            className="absolute bottom-4 left-1/2 -translate-x-1/2 z-floating flex h-9 w-9 items-center justify-center rounded-full border border-line-2 bg-surface text-foreground-secondary shadow-lg hover:bg-bg-3 hover:text-foreground transition-colors"
            title="Retour en bas"
            aria-label="Retour en bas"
          >
            <ArrowDown size={16} />
          </button>
        )}
      </div>

      {/* Bannière d'erreur — non bloquante, dismissable */}
      {errorBanner}

      {/* Composer */}
      {composer}
    </div>
  );
}
