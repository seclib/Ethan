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
    <div className="w-64 border-l border-gray-800 bg-gray-900/30 flex flex-col">
      {/* Tabs */}
      <div className="flex border-b border-gray-800">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`flex-1 px-2 py-2 text-xs text-center transition-colors ${
              activeTab === tab.id
                ? "text-white border-b-2 border-blue-500 bg-gray-800/50"
                : "text-gray-500 hover:text-gray-300"
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
            ? <p className="text-xs text-gray-500">Aucun document</p>
            : documents.map((doc, i) => (
                <div key={i} className="text-xs text-gray-400 p-2 rounded bg-gray-800/30">
                  <p className="text-gray-300">{doc.name}</p>
                  <p className="text-gray-500">{(doc.size / 1024).toFixed(0)} KB · {doc.type}</p>
                </div>
              ))
        )}

        {activeTab === "memory" && (
          memoryEntries.length === 0
            ? <p className="text-xs text-gray-500">Aucune entrée mémoire</p>
            : memoryEntries.map((entry, i) => (
                <div key={i} className="text-xs text-gray-400 p-2 rounded bg-gray-800/30">
                  <div className="flex justify-between">
                    <span className="text-gray-300">{entry.key}</span>
                    <span className="text-yellow-400">{Math.round(entry.relevance * 100)}%</span>
                  </div>
                  <p className="text-gray-500 truncate mt-1">{entry.snippet}</p>
                </div>
              ))
        )}

        {activeTab === "tools" && (
          tools.length === 0
            ? <p className="text-xs text-gray-500">Aucun outil appelé</p>
            : tools.map((tool, i) => (
                <div key={i} className="text-xs text-gray-400 p-2 rounded bg-gray-800/30 flex justify-between">
                  <span className="text-gray-300">{tool.name}</span>
                  <span className="text-gray-500">{(tool.durationMs / 1000).toFixed(1)}s</span>
                </div>
              ))
        )}

        {activeTab === "mcp" && (
          mcpCalls.length === 0
            ? <p className="text-xs text-gray-500">Aucune connexion MCP</p>
            : mcpCalls.map((call, i) => (
                <div key={i} className="text-xs text-gray-400 p-2 rounded bg-gray-800/30">
                  <div className="flex justify-between">
                    <span className="text-gray-300">{call.tool}</span>
                    <span className={call.status === "success" ? "text-green-400" : "text-red-400"}>{call.status}</span>
                  </div>
                  <p className="text-gray-500">{call.server} · {(call.durationMs / 1000).toFixed(1)}s</p>
                </div>
              ))
        )}

        {activeTab === "actions" && (
          actions.length === 0
            ? <p className="text-xs text-gray-500">Aucune action</p>
            : actions.map((action, i) => (
                <div key={i} className="text-xs text-gray-400 p-2 rounded bg-gray-800/30">
                  <div className="flex justify-between">
                    <span className="text-gray-300">{action.description}</span>
                    <span className={
                      action.status === "done" ? "text-green-400" :
                      action.status === "running" ? "text-blue-400" :
                      action.status === "error" ? "text-red-400" : "text-gray-500"
                    }>{action.status}</span>
                  </div>
                  <p className="text-gray-500">{action.type}</p>
                </div>
              ))
        )}
      </div>
    </div>
  );
}