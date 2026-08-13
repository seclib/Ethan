"use client";

import * as React from "react";
import { useChats, type EthChat } from "@/features/assistant/hooks/use-chats";

interface ChatSidebarProps {
  className?: string;
}

/**
 * Panneau latéral des conversations inspiré d'Open-WebUI.
 * - Liste les conversations persistées via core/state/chats.py
 * - Créer / sélectionner / supprimer / rechercher
 * ETHAN Core est la source de vérité — la WebUI ne fait qu'afficher/agir.
 */
export function ChatSidebar({ className = "" }: ChatSidebarProps) {
  const { chats, currentChatId, selectChat, createChat, deleteChat } = useChats();
  const [search, setSearch] = React.useState("");

  const filtered = chats.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase())
  );

  const handleNewChat = () => {
    createChat("Nouvelle conversation");
  };

  const handleDelete = (e: React.MouseEvent, chat: EthChat) => {
    e.stopPropagation();
    deleteChat(chat.id);
  };

  return (
    <aside className={`w-64 shrink-0 border-r border-line-2 bg-background/40 flex flex-col ${className}`}>
      {/* Header */}
      <div className="p-3 border-b border-line-1/20">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 rounded-md border border-accent/50 bg-accent/10 px-3 py-2 text-sm font-medium text-foreground hover:bg-accent/20 transition-colors"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nouveau chat
        </button>
      </div>

      {/* Recherche */}
      <div className="p-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Rechercher..."
          className="w-full rounded-md border border-line-1/20 bg-background/20 px-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-accent transition-colors"
        />
      </div>

      {/* Liste des conversations */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filtered.length === 0 && (
          <div className="px-2 py-4 text-center text-sm text-muted-foreground">
            {search ? "Aucune conversation trouvée" : "Aucune conversation"}
          </div>
        )}
        {filtered.map((chat) => (
          <div
            key={chat.id}
            onClick={() => selectChat(chat.id)}
            className={`group flex items-center gap-2 rounded-md px-2 py-1.5 cursor-pointer transition-colors ${
              currentChatId === chat.id
                ? "bg-accent/20 text-foreground"
                : "hover:bg-bg-2 text-foreground-secondary"
            }`}
          >
            <svg className="h-4 w-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span className="flex-1 truncate text-sm">{chat.title}</span>
            <button
              onClick={(e) => handleDelete(e, chat)}
              className="hidden group-hover:block p-1 rounded hover:bg-bg-1 text-muted-foreground hover:text-red-400 shrink-0"
              title="Supprimer"
            >
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}