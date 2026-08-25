"use client";

/**
 * Page Inbox — boîte mail lecture seule (RFC-0001).
 * IMAP géré par ETHAN Core (core/mailbox) ; la page ne fait que rendre.
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  listEmailMessages, getEmailMessage, type EmailSummary,
} from "@/lib/api/extensions";
import { Inbox, RefreshCw, MailOpen } from "lucide-react";

export default function InboxPage() {
  const [selected, setSelected] = React.useState<string | null>(null);

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
    <div className="flex h-full min-h-0 flex-col">
      <header style={{ padding: "16px 24px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 18, color: "var(--fg)" }}>
          <Inbox size={18} /> Boîte de réception
        </h1>
        <button
          className="icon-rail-btn"
          title="Rafraîchir"
          onClick={() => messages.refetch()}
          style={{ width: 32, height: 32 }}
        >
          <RefreshCw size={14} />
        </button>
      </header>

      {notConfigured ? (
        <div style={{ padding: 24, fontSize: 13, opacity: 0.8, maxWidth: 640 }}>
          <p style={{ marginBottom: 12 }}>📬 La boîte mail n&apos;est pas configurée.</p>
          <p style={{ marginBottom: 8 }}>Définir dans l&apos;environnement du service API :</p>
          <pre style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 12, fontSize: 12 }}>
{`ETHAN_EMAIL_IMAP_HOST=imap.exemple.com
ETHAN_EMAIL_IMAP_PORT=993
ETHAN_EMAIL_USER=moi@exemple.com
ETHAN_EMAIL_PASSWORD=***   # via secret manager, jamais en git
ETHAN_EMAIL_FOLDER=INBOX`}
          </pre>
        </div>
      ) : (
        <div style={{ flex: 1, minHeight: 0, display: "flex" }}>
          {/* Liste */}
          <div className="custom-scrollbar sidebar-inner" style={{ width: 360, borderRight: "1px solid var(--border)", overflowY: "auto" }}>
            {messages.isLoading && <p style={{ padding: 16, opacity: 0.6 }}>Chargement…</p>}
            {messages.data?.length === 0 && <p style={{ padding: 16, opacity: 0.6 }}>Boîte vide.</p>}
            {(messages.data ?? []).map((m: EmailSummary) => (
              <button
                key={m.uid}
                onClick={() => setSelected(m.uid)}
                className={`list-item ${selected === m.uid ? "active" : ""}`}
                style={{ display: "block", textAlign: "left", width: "100%", padding: "10px 12px" }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                  <strong style={{ fontSize: 12 }}>{m.from_name || m.from}</strong>
                  <span style={{ fontSize: 10, opacity: 0.6, whiteSpace: "nowrap" }}>
                    {m.date?.slice(0, 16).replace("T", " ")}
                  </span>
                </div>
                <div style={{ fontSize: 12, opacity: 0.85 }}>{m.subject || "(sans objet)"}</div>
              </button>
            ))}
          </div>

          {/* Lecture */}
          <div className="custom-scrollbar" style={{ flex: 1, overflowY: "auto", padding: 24 }}>
            {!selected && <p style={{ opacity: 0.5, display: "flex", gap: 8, alignItems: "center" }}><MailOpen size={16} /> Sélectionner un message</p>}
            {detail.isLoading && <p style={{ opacity: 0.6 }}>Chargement…</p>}
            {detail.data && (
              <article style={{ maxWidth: 760 }}>
                <h2 style={{ fontSize: 16, color: "var(--fg)" }}>{detail.data.subject}</h2>
                <p style={{ fontSize: 12, opacity: 0.65, margin: "6px 0 16px" }}>
                  De : {detail.data.from} · À : {detail.data.to} · {detail.data.date?.slice(0, 19).replace("T", " ")}
                </p>
                <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: 13, lineHeight: 1.55 }}>
                  {detail.data.body}
                </pre>
              </article>
            )}
            {detail.isError && <p style={{ color: "var(--red)" }}>Impossible de charger le message.</p>}
          </div>
        </div>
      )}
    </div>
  );
}