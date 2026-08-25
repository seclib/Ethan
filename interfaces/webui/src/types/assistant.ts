export interface DocumentRef {
  name: string;
  type: string;
  size: number;
  url?: string;
}

export interface ToolCall {
  name: string;
  durationMs: number;
  status: "success" | "error";
  result?: string;
}

export interface MemoryRef {
  key: string;
  relevance: number;
  snippet: string;
}

export interface McpCall {
  tool: string;
  server: string;
  durationMs: number;
  status: "success" | "error";
}

export interface AgentAction {
  type: string;
  description: string;
  status: "pending" | "running" | "done" | "error";
}

export interface AssistantMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;

  /** État du message : pending (génération), done, stopped, error. */
  status?: string;
  done?: boolean;

  // Assistant only
  reasoning?: string[];
  documents?: DocumentRef[];
  tools?: ToolCall[];
  memoryEntries?: MemoryRef[];
  mcpCalls?: McpCall[];
  actions?: AgentAction[];

  // Metrics
  durationMs?: number;
  cost?: number;
  tokensUsed?: number;
  tokensTotal?: number;
  model?: string;
  provider?: string;
}

export interface SessionMetrics {
  agentName: string;
  agentStatus: "run" | "idle" | "error";
  model: string;
  provider: string;
  cost: number;
  duration: number;
  tokensUsed: number;
  tokensTotal: number;
}

export type SidePanelTab = "documents" | "memory" | "tools" | "mcp" | "actions";