"use client";

/**
 * FLUX MAIL PANEL
 * Rendu minimal du backend Core (core/mailbox via /v1/email).
 * Inspiré du pattern Odysseus *mail-overlay*.
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listEmailMessages, getEmailMessage, EmailSummary } from "@/lib/api/extensions";
import { Inbox, RefreshCw, MailOpen } from "lucide-react";
import { Button } from "@/components/ui/button";

export function MailPanel() {
  const [selected, setSelected] = useState<string | null>(null);

  const messages = useQuery({
    queryKey: ["email-messages"],
    queryFn: () => listEmailMessages(30),
    retry: false,
  });

  const detail = useQuery({
    queryKey: ["email-message", selected],
    queryFn: () => getEmailMessage(selected!),
    enabled: !!selected,
    retry: false,
  });

  const notConfigured = messages.isError && /configur/i.test(String(messages.error));

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-line-1 bg-elevated/30">
        <span className="text-xs font-medium text-foreground-secondary flex items-center gap-1">
          <Inbox size={14} /> Boîte de réception
          {/* Audit UX P2-3 : le backend n'expose que GET /v1/email/messages —
              l'affichage honnête de la portée évite toute action attendue et
              impossible (marquer lu, supprimer…). */}
          <span
            className="ml-1 text-[9px] font-medium text-foreground-tertiary border border-line-2 rounded px-1 py-px"
            title="Lecture seule : le Core n'expose pas encore d'actions d'écriture"
          >
            lecture seule
          </span>
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          title="Rafraîchir"
          aria-label="Rafraîchir"
          onClick={() => messages.refetch()}
        >
          <RefreshCw size={12} />
        </Button>
      </div>

      {notConfigured ? (
        <div className="p-3 text-[11px] text-foreground-secondary flex items-start gap-2">
          <span className="text-warning">⚠</span>
          <div>
            La boîte mail n&apos;est pas configurée (RFC-0001).
          </div>
        </div>
      ) : (
        <div className="flex flex-1 min-h-0">
          <div className="w-44 overflow-y-auto border-r border-line-1">
            {messages.isLoading && <p className="p-3 text-[11px] opacity-50">Chargement…</p>}
            {messages.data?.length === 0 && <p className="p-3 text-[11px] opacity-50">Boîte vide.</p>}
            {(messages.data ?? []).map((m: EmailSummary) => (
              <button
                key={m.uid}
                onClick={() => setSelected(m.uid)}
                className={`block w-full text-left px-3 py-2 border-b border-line-1/30 ${selected === m.uid ? "bg-accent/10" : "hover:bg-elevated/30"} transition-colors`}
              >
                <div className="flex justify-between gap-2">
                  <strong className="text-[11px] truncate">{m.from_name || m.from}</strong>
                  <span className="text-[9px] opacity-50 whitespace-nowrap">
                    {m.date?.slice(0, 16).replace("T", " ")}
                  </span>
                </div>
                <div className="text-[10px] opacity-70 truncate">{m.subject || "(sans objet)"}</div>
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-3">
            {!selected && (
              <p className="flex items-center gap-1 text-[11px] opacity-40">
                <MailOpen size={14} /> Sélectionner un message
              </p>
            )}
            {detail.isLoading && <p className="text-[11px] opacity-50">Chargement…</p>}
            {detail.data && (
              <article>
                <h2 className="text-[12px] font-medium text-foreground mb-1">
                  {detail.data.subject}
                </h2>
                <p className="text-[10px] opacity-50 mb-3">
                  De : {detail.data.from} · À : {detail.data.to} ·{" "}
                  {detail.data.date?.slice(0, 19).replace("T", " ")}
                </p>
                <pre className="text-[11px] leading-relaxed whitespace-pre-wrap">
                  {detail.data.body}
                </pre>
              </article>
            )}
          </div>
        </div>
      )}
    </div>
  );
}