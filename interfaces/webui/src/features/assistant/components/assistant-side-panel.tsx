"use client";

import { useState } from "react";
import type { SidePanelTab, DocumentRef, MemoryRef, ToolCall, McpCall, AgentAction } from "@/types/assistant";

interface AssistantSidePanelProps {
  documents: DocumentRef[];
  memoryEntries: MemoryRef[];
  tools: ToolCall[];
  mcpCalls: McpCall[];
  actions: AgentAction[];
}

const TABS: { id: SidePanelTab; label: string; icon: string }[] = [
  { id: "documents", label: "Documents", icon: "📄" },
  { id: "memory", label: "Mémoire", icon: "🧠" },
  { id: "tools", label: "Outils", icon: "🔧" },
  { id: "mcp", label: "MCP", icon: "🔌" },
  { id: "actions", label: "Actions", icon: "⚡" },
];

export function AssistantSidePanel({ documents, memoryEntries, tools, mcpCalls, actions }: AssistantSidePanelProps) {
  const [activeTab, setActiveTab] = useState<SidePanelTab>("documents");

  return (
    <div className="hidden w-64 shrink-0 flex-col border-l border-line-2 bg-background/30 md:flex">
      {/* Tabs */}
      <div className="flex border-b border-line-2">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`flex-1 px-2 py-2 text-xs text-center transition-colors ${
              activeTab === tab.id
                ? "text-foreground border-b-2 border-accent bg-line-1/20"
                : "text-muted-foreground hover:text-foreground/70"
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            <div>{tab.icon}</div>
            <div className="mt-0.5">{tab.label}</div>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {activeTab === "documents" && (
          documents.length === 0
            ? <p className="text-xs text-muted-foreground">Aucun document</p>
            : documents.map((doc, i) => (
                <div key={i} className="text-xs text-muted-foreground/70 p-2 rounded bg-background/20">
                  <p className="text-foreground/70">{doc.name}</p>
                  <p className="text-muted-foreground">{(doc.size / 1024).toFixed(0)} KB · {doc.type}</p>
                </div>
              ))
        )}

        {activeTab === "memory" && (
          memoryEntries.length === 0
            ? <p className="text-xs text-muted-foreground">Aucune entrée mémoire</p>
            : memoryEntries.map((entry, i) => (
                <div key={i} className="text-xs text-muted-foreground/70 p-2 rounded bg-background/20">
                  <div className="flex justify-between">
                    <span className="text-foreground/70">{entry.key}</span>
                    <span className="text-amber-400">{Math.round(entry.relevance * 100)}%</span>
                  </div>
                  <p className="text-muted-foreground truncate mt-1">{entry.snippet}</p>
                </div>
              ))
        )}

        {activeTab === "tools" && (
          tools.length === 0
            ? <p className="text-xs text-muted-foreground">Aucun outil appelé</p>
            : tools.map((tool, i) => (
                <div key={i} className="text-xs text-muted-foreground/70 p-2 rounded bg-background/20 flex justify-between">
                  <span className="text-foreground/70">{tool.name}</span>
                  <span className="text-muted-foreground">{(tool.durationMs / 1000).toFixed(1)}s</span>
                </div>
              ))
        )}

        {activeTab === "mcp" && (
          mcpCalls.length === 0
            ? <p className="text-xs text-muted-foreground">Aucune connexion MCP</p>
            : mcpCalls.map((call, i) => (
                <div key={i} className="text-xs text-muted-foreground/70 p-2 rounded bg-background/20">
                  <div className="flex justify-between">
                    <span className="text-foreground/70">{call.tool}</span>
                    <span className={call.status === "success" ? "text-green-400" : "text-red-400"}>{call.status}</span>
                  </div>
                  <p className="text-muted-foreground">{call.server} · {(call.durationMs / 1000).toFixed(1)}s</p>
                </div>
              ))
        )}

        {activeTab === "actions" && (
          actions.length === 0
            ? <p className="text-xs text-muted-foreground">Aucune action</p>
            : actions.map((action, i) => (
                <div key={i} className="text-xs text-muted-foreground/70 p-2 rounded bg-background/20">
                  <div className="flex justify-between">
                    <span className="text-foreground/70">{action.description}</span>
                    <span className={
                      action.status === "done" ? "text-green-400" :
                      action.status === "running" ? "text-accent" :
                      action.status === "error" ? "text-red-400" : "text-muted-foreground"
                    }>{action.status}</span>
                  </div>
                  <p className="text-muted-foreground">{action.type}</p>
                </div>
              ))
        )}
      </div>
    </div>
  );
}
