const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export interface SystemState {
  mode: string;
  active_goal: string;
  running_tasks: number;
  last_event: Record<string, unknown> | null;
  modules: number;
  uptime: string;
}

export interface Event {
  id: string;
  type: string;
  source: string;
  timestamp: string;
  data: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface Goal {
  id: string;
  description: string;
  status: string;
  priority: string;
  progress: number;
  created_at: string;
}

export interface AuditEntry {
  id: string;
  category: string;
  decision: string;
  action: string;
  actor: string;
  timestamp: string;
  details: Record<string, unknown>;
}

export interface BudgetEntry {
  id: string;
  category: string;
  amount: number;
  description: string;
  timestamp: string;
}

export interface Fact {
  id: string;
  subject: string;
  predicate: string;
  object: string;
  category: string;
  status: string;
  confidence: number;
  created_at: string;
}

export interface ApprovalRequest {
  request_id: string;
  title: string;
  category: string;
  source: string;
  timeout_seconds: number;
  description: string;
}

export interface SkillTestResult {
  id: string;
  skill_name: string;
  status: string;
  passed: boolean;
  duration_ms: number;
  output: string;
  error: string;
}

async function fetchJSON<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  // State
  getState: () => fetchJSON<SystemState>("/state"),

  // Events
  getEvents: (limit = 50) =>
    fetchJSON<{ events: Event[] }>(`/events?limit=${limit}`),

  // Goals
  getGoals: () => fetchJSON<{ goals: Goal[] }>("/goals"),

  // Chat
  sendMessage: (content: string) =>
    fetchJSON<{ response: string }>("/message", {
      method: "POST",
      body: JSON.stringify({ content }),
    }),

  sendMessageStream: (content: string) => {
    return fetch(`${API_BASE}/message/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    }).then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.body as ReadableStream<Uint8Array>;
    });
  },

  // Logs
  getLogs: () => fetchJSON<{ logs: Record<string, unknown>[] }>("/logs"),

  // Internal — Audit
  getAudit: (limit = 50) =>
    fetchJSON<AuditEntry[]>(`/internal/audit/recent?limit=${limit}`),
  searchAudit: (q: string) =>
    fetchJSON<AuditEntry[]>(`/internal/audit/search?q=${encodeURIComponent(q)}`),

  // Internal — Budget
  getBudget: (limit = 50) =>
    fetchJSON<BudgetEntry[]>(`/internal/budget/recent?limit=${limit}`),
  getBudgetSummary: () =>
    fetchJSON<{ total: number; by_category: Record<string, number> }>(
      "/internal/budget/summary"
    ),

  // Internal — Facts
  getFacts: (limit = 50) =>
    fetchJSON<Fact[]>(`/internal/facts/recent?limit=${limit}`),
  searchFacts: (q: string) =>
    fetchJSON<Fact[]>(`/internal/facts/search?q=${encodeURIComponent(q)}`),

  // Internal — Approval
  getPendingApprovals: () =>
    fetchJSON<ApprovalRequest[]>("/internal/approval/pending"),
  resolveApproval: (requestId: string, approved: boolean, reason = "") =>
    fetchJSON<{ success: boolean }>("/internal/approval/resolve", {
      method: "POST",
      body: JSON.stringify({
        request_id: requestId,
        approved,
        reason,
        responder: "human",
      }),
    }),

  // Internal — SkillLab
  testSkill: (name: string, code: string, input = "", requirements: string[] = []) =>
    fetchJSON<SkillTestResult>("/internal/skilllab/test", {
      method: "POST",
      body: JSON.stringify({ name, code, input, requirements }),
    }),
  getSkillResults: () =>
    fetchJSON<SkillTestResult[]>("/internal/skilllab/results"),
};