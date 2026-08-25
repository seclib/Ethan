// ============================================================================
// ETHAN WebUI — Type Definitions
// ============================================================================

// ── Agent ───────────────────────────────────────────────────────────────────

export interface Agent {
  id: string;
  name: string;
  description?: string;
  capabilities: string[];
  status: AgentStatus;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
  model?: string;
  provider?: string;
  skill_ids?: string[];
  memory_scope?: string;
}

export type AgentStatus = "idle" | "running" | "paused" | "error" | "stopped";

// ── Goal ────────────────────────────────────────────────────────────────────

export interface Goal {
  id: string;
  title: string;
  description?: string;
  priority: GoalPriority;
  status: GoalStatus;
  tasks: Task[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export type GoalPriority = "low" | "medium" | "high" | "critical";
export type GoalStatus = "pending" | "active" | "paused" | "completed" | "failed" | "cancelled";

// ── Task ────────────────────────────────────────────────────────────────────

export interface Task {
  id: string;
  goal_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  depends_on: string[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
  result?: any;
  error?: string;
}

export type TaskStatus = "pending" | "running" | "completed" | "failed" | "cancelled" | "skipped";

// ── Mission ─────────────────────────────────────────────────────────────────

export interface Mission {
  id: string;
  title: string;
  description: string;
  status: MissionStatus;
  steps: Step[];
  steps_total?: number;
  steps_completed?: number;
  workspace_path: string;
  artifacts: Record<string, any>;
  logs: LogEntry[];
  verdict?: MissionVerdict;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export type MissionStatus = "pending" | "planning" | "running" | "paused" | "completed" | "failed" | "killed";
export type MissionVerdict = "success" | "failure" | "partial" | "killed";

// ── Step ────────────────────────────────────────────────────────────────────

export interface Step {
  id: string;
  mission_id: string;
  title: string;
  description: string;
  status: StepStatus;
  success_criterion: string;
  verification_command?: string;
  access_level: AccessLevel;
  verified: boolean;
  verification_notes?: string;
  depends_on: string[];
  order: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  result?: any;
  error?: string;
}

export type StepStatus = "pending" | "running" | "completed" | "failed" | "cancelled" | "skipped" | "waiting_approval";

// ── Memory ──────────────────────────────────────────────────────────────────

export interface Fact {
  id: string;
  subject: string;
  predicate: string;
  object: string;
  category: FactCategory;
  status: FactStatus;
  confidence: number;
  support_count: number;
  decay_policy: DecayPolicy;
  valid_from: string;
  valid_to?: string;
  source_event_id: string;
  created_at: string;
  last_seen_at: string;
  updated_at: string;
}

export type FactCategory =
  | "identity"
  | "preference"
  | "project"
  | "goal"
  | "habit"
  | "constraint"
  | "belief"
  | "relationship"
  | "tool"
  | "persona"
  | "decision"
  | "health_fitness"
  | "work_style"
  | "memory_correction";

export type FactStatus = "active" | "superseded" | "conflicted" | "archived" | "needs_review";
export type DecayPolicy = "none" | "very_slow" | "slow" | "medium" | "fast";

export interface MemoryEvent {
  id: string;
  type: string;
  source: string;
  content: string;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface FactObservation {
  id: string;
  fact_id: string;
  event_id: string;
  observation_type: ObservationType;
  confidence_delta: number;
  created_at: string;
}

export type ObservationType = "confirm" | "weaken" | "correct";

export interface FactRelation {
  id: string;
  from_fact_id: string;
  to_fact_id: string;
  relation_type: RelationType;
  created_at: string;
}

export type RelationType = "supersedes" | "contradicts" | "supports" | "related_to";

// ── Skill ───────────────────────────────────────────────────────────────────

export interface Skill {
  id: string;
  name: string;
  description: string;
  version: string;
  status: SkillStatus;
  confidence: number;
  support_count: number;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
  path: string;
  metadata?: Record<string, any>;
}

export type SkillStatus = "candidate" | "active" | "stale" | "archived";

// ── Flux / Events ───────────────────────────────────────────────────────────

export interface FluxEvent {
  id: string;
  type: string;
  source: string;
  payload: Record<string, any>;
  timestamp: string;
}

// ── User & Auth ─────────────────────────────────────────────────────────────

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  permissions: Permission[];
  created_at: string;
}

export type UserRole = "user" | "admin" | "superadmin";

export interface Permission {
  resource: string;
  actions: string[];
}

// ── Settings ────────────────────────────────────────────────────────────────

export interface Settings {
  llm: LLMSettings;
  permissions: PermissionsConfig;
  governance: GovernanceConfig;
  budget: BudgetConfig;
  system: SystemConfig;
}

export interface SystemConfig {
  log_level: string;
  max_workers: number;
}

export interface LLMSettings {
  backend: LLMBackend;
  model: string;
  temperature: number;
  max_tokens: number;
  api_key?: string;
}

export type LLMBackend = "anthropic" | "openai" | "mistral" | "local" | "gemini";

export interface PermissionsConfig {
  approvals: ApprovalConfig[];
}

export interface ApprovalConfig {
  category: string;
  mode: ApprovalMode;
  description?: string;
}

export type ApprovalMode = "ALWAYS" | "ASK" | "NEVER";

export interface GovernanceConfig {
  access_levels: AccessLevelConfig[];
  autonomy_levels: AutonomyLevelConfig[];
}

export interface AccessLevelConfig {
  level: AccessLevel;
  name: string;
  description: string;
}

export type AccessLevel = 0 | 1 | 2 | 3 | 4 | 5;

export interface AutonomyLevelConfig {
  level: number;
  name: string;
  description: string;
  requires_approval: boolean;
}

export interface BudgetConfig {
  daily_limit_usd: number;
  mission_limit_usd: number;
  warning_threshold: number;
  hard_stop_threshold: number;
}

// ── Vocabulaire fermé (Jarvis-OS inspired) ───────────────────────────────────

export const PREDICATES = [
  "is",
  "has",
  "prefers",
  "dislikes",
  "uses",
  "works_on",
  "targets",
  "plans",
  "believes",
  "needs",
  "struggles_with",
  "decided",
  "changed",
  "values",
  "communicates_as",
  "requires_validation_for",
] as const;

export const CATEGORIES = [
  "identity",
  "preference",
  "project",
  "goal",
  "habit",
  "constraint",
  "belief",
  "relationship",
  "tool",
  "persona",
  "decision",
  "health_fitness",
  "work_style",
  "memory_correction",
] as const;

// ── API Response wrappers ────────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ── UI State ────────────────────────────────────────────────────────────────

export interface Toast {
  id: string;
  type: "info" | "success" | "warning" | "error";
  message: string;
  duration?: number;
}

export type Theme = "dark" | "light" | "system";

// ── WebSocket Events ─────────────────────────────────────────────────────────

export type WebSocketEvent =
  | { type: "subscribe"; channel: string }
  | { type: "unsubscribe"; channel: string }
  | { type: "mission.updated"; payload: Mission }
  | { type: "step.verified"; payload: Step }
  | { type: "fact.ingested"; payload: Fact }
  | { type: "skill.installed"; payload: Skill }
  | { type: "notification"; payload: { message: string; priority: string } }
  | { type: "error"; payload: { message: string } };

// ── Log Entry ────────────────────────────────────────────────────────────────

export interface LogEntry {
  timestamp: string;
  level: string;
  source: string;
  message: string;
  metadata?: Record<string, any>;
}

// ── Governance ──────────────────────────────────────────────────────────────

export interface GateDecision {
  decision: "auto" | "dry_run" | "approval" | "refused";
  reason: string;
  axes: {
    risk: { level: AccessLevel; decision: string };
    category: { mode: ApprovalMode; decision: string };
    budget: { status: string; decision: string };
  };
}