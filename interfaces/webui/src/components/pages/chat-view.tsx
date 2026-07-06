"use client";

import { useState } from "react";

const MESSAGES = [
  { role: "user", content: "Déploie la v2.1 sur staging" },
  { role: "system", content: "Goal créé: GOAL-001. Plan: 5 étapes, estimation 2m30s." },
  { role: "user", content: "Quel est le statut du déploiement ?" },
  { role: "system", content: "Étape 3/5 en cours. Budget: 1.2k/2.0k tokens." },
];

export function ChatViewPage() {
  const [input, setInput] = useState("");

  return (
    <div className="page-chat">
      <div className="chat-header">
        <h1 className="page-title">Chat</h1>
        <div className="chat-meta">
          <span>Session: a1b2c3d4</span>
          <span>Contexte: 12 items</span>
        </div>
      </div>

      <div className="chat-messages">
        {MESSAGES.map((m, i) => (
          <div key={i} className={`chat-message chat-${m.role}`}>
            <div className="chat-role">{m.role === "user" ? "Vous" : "ETHAN"}</div>
            <div className="chat-content">{m.content}</div>
          </div>
        ))}
      </div>

      <div className="chat-input-row">
        <input
          className="chat-input"
          placeholder="Nouveau message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && setInput("")}
        />
        <button className="btn btn-primary" onClick={() => setInput("")}>Envoyer</button>
      </div>

      <div className="chat-quick-actions">
        <span className="chat-quick-hint">Quick actions:</span>
        <button className="btn btn-ghost">/goal</button>
        <button className="btn btn-ghost">/mission</button>
        <button className="btn btn-ghost">/status</button>
        <button className="btn btn-ghost">/logs</button>
      </div>
    </div>
  );
}