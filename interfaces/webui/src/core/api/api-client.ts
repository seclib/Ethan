/**
 * Centralized API client with interceptors
 *
 * Toutes les requêtes utilisent des URLs relatives (/api/*) qui traversent le
 * proxy Next.js défini dans next.config.js.  Le proxy effectue le rewriting
 * /api/* → ETHAN_API_URL/* et supprime le préfixe /api.
 *
 * En développement, ETHAN_API_URL vaut http://localhost:8000.
 * En Docker, il vaut http://api:8000 (défini dans docker-compose.yml).
 */

import type {
  Provider,
  ProviderCreate,
  ProviderUpdate,
  ProviderModel,
  TestConnectionResult,
} from "./providers.types";

export interface RagDocument {
  id: string;
  title: string;
  source: string;
  content: string;
  chunks: Array<{ id: string; content: string; order: number }>;
  metadata: Record<string, unknown>;
}

const API_BASE_URL = ""; // URLs relatives → passent par le proxy Next.js

class ApiClient {
  private baseURL: string;
  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string> | undefined),
    };

    const config: RequestInit = {
      credentials: "include",
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 Unauthorized
      if (response.status === 401) {
        throw new Error("Unauthorized");
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          message: `HTTP ${response.status}: ${response.statusText}`,
        }));
        throw new Error(error.message || error.error || "Request failed");
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return {} as T;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("Unknown error occurred");
    }
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.request<{ token: string; user: any }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: email, password }),
    });
  }

  async logout() {
    return this.request<void>("/api/auth/logout", {
      method: "POST",
    });
  }

  async refreshToken() {
    return this.request<{ token: string }>("/api/auth/refresh", {
      method: "POST",
    });
  }

  async getCurrentUser() {
    return this.request<any>("/api/auth/me");
  }

  // Agents endpoints
  async getAgents() {
    return this.request<any[]>("/api/v1/agents");
  }

  async getAgent(id: string) {
    return this.request<any>(`/api/v1/agents/${id}`);
  }

  async createAgent(data: { name: string; capabilities?: string[] }) {
    return this.request<any>("/api/v1/agents", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateAgent(id: string, data: Partial<any>) {
    return this.request<any>(`/api/v1/agents/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteAgent(id: string) {
    return this.request<void>(`/api/v1/agents/${id}`, {
      method: "DELETE",
    });
  }

  // Goals endpoints
  async getGoals() {
    return this.request<any[]>("/api/v1/goals");
  }

  async getGoal(id: string) {
    return this.request<any>(`/api/v1/goals/${id}`);
  }

  async createGoal(data: { title: string; description?: string; priority?: string }) {
    return this.request<any>("/api/v1/goals", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateGoal(id: string, data: Partial<any>) {
    return this.request<any>(`/api/v1/goals/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteGoal(id: string) {
    return this.request<void>(`/api/v1/goals/${id}`, {
      method: "DELETE",
    });
  }

  // Memory endpoints
  async searchMemory(query: string, filters?: any) {
    const params = new URLSearchParams({ query, ...filters });
    return this.request<any>(`/api/v1/memory/search?${params}`);
  }

  async storeMemory(entry: any) {
    return this.request<any>("/api/v1/memory/ingest", {
      method: "POST",
      body: JSON.stringify(entry),
    });
  }

  async getMemoryEntry(id: string) {
    return this.request<any>(`/api/v1/memory/${id}`);
  }

  // RAG document endpoints. The WebUI remains a client: chunking, embeddings,
  // retrieval and persistence all stay in core/rag.
  async getRagDocuments() {
    return this.request<RagDocument[]>("/api/v1/rag/documents");
  }

  async ingestRagDocument(data: {
    title?: string;
    source?: string;
    content: string;
    metadata?: Record<string, unknown>;
  }) {
    return this.request<RagDocument>("/api/v1/rag/documents", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Skills endpoints
  async getSkills() {
    return this.request<any[]>("/api/v1/skills");
  }

  async getSkill(id: string) {
    return this.request<any>(`/api/v1/skills/${id}`);
  }

  async executeSkill(id: string, params: any) {
    return this.request<any>(`/api/v1/skills/${id}/execute`, {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Flux endpoints
  async getFluxEvents(filters?: any) {
    const params = new URLSearchParams(filters);
    return this.request<any[]>(`/api/v1/flux?${params}`);
  }

  // Settings endpoints
  async getSettings() {
    return this.request<any>("/api/v1/settings");
  }

  async updateSettings(data: any) {
    return this.request<any>("/api/v1/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  // ── LLM Providers endpoints ───────────────────────────────────────────
  // Backend routes are mounted at /providers/* (the Next.js proxy rewrites
  // /api/* → ETHAN_API_URL/*, stripping the /api prefix).
  async getProviders() {
    return this.request<Provider[]>("/api/providers");
  }

  async createProvider(data: ProviderCreate) {
    return this.request<Provider>("/api/providers", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateProvider(id: string, data: ProviderUpdate) {
    return this.request<Provider>(`/api/providers/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteProvider(id: string) {
    return this.request<{ status: string; provider_id: string }>(`/api/providers/${id}`, {
      method: "DELETE",
    });
  }

  async getProviderModels(id: string) {
    return this.request<ProviderModel[]>(`/api/providers/${id}/models`);
  }

  async testProviderConnection(id: string) {
    return this.request<TestConnectionResult>(`/api/providers/${id}/test`, {
      method: "POST",
    });
  }

  async setDefaultProvider(id: string) {
    return this.request<Provider>(`/api/providers/${id}/default`, {
      method: "PUT",
    });
  }

  // ── Chats endpoints (persistance via core/state/chats.py) ─────────────
  async getChats(params?: { user_id?: string; archived?: boolean }) {
    const qs = new URLSearchParams();
    if (params?.user_id) qs.set("user_id", params.user_id);
    if (params?.archived !== undefined) qs.set("archived", String(params.archived));
    const suffix = qs.toString() ? `?${qs}` : "";
    return this.request<any[]>("/api/chats" + suffix);
  }

  async createChat(data: { title: string; user_id?: string; folder_id?: string; metadata?: Record<string, unknown> }) {
    return this.request<any>("/api/chats", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getChat(id: string) {
    return this.request<any>(`/api/chats/${id}`);
  }

  async updateChat(id: string, data: Record<string, unknown>) {
    return this.request<any>(`/api/chats/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteChat(id: string) {
    return this.request<{ status: string }>(`/api/chats/${id}`, {
      method: "DELETE",
    });
  }

  async getChatMessages(chatId: string) {
    return this.request<any[]>(`/api/chats/${chatId}/messages`);
  }

  async addChatMessage(chatId: string, data: { role: string; content: string; user_id?: string; metadata?: Record<string, unknown> }) {
    return this.request<any>(`/api/chats/${chatId}/messages`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async shareChat(chatId: string) {
    return this.request<any>(`/api/chats/${chatId}/share`, {
      method: "POST",
    });
  }

  // ── Capabilities endpoints (exposées par le router capabilities.py) ──────
  // Automations
  async getAutomations(enabled?: boolean) {
    const qs = enabled !== undefined ? `?enabled=${enabled}` : "";
    return this.request<any[]>(`/api/v1/automations${qs}`);
  }

  async createAutomation(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/automations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getAutomation(id: string) {
    return this.request<any>(`/api/v1/automations/${id}`);
  }

  async updateAutomation(id: string, data: Record<string, unknown>) {
    return this.request<any>(`/api/v1/automations/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteAutomation(id: string) {
    return this.request<any>(`/api/v1/automations/${id}`, {
      method: "DELETE",
    });
  }

  async triggerAutomation(id: string) {
    return this.request<any>(`/api/v1/automations/${id}/trigger`, {
      method: "POST",
    });
  }

  // Calendar
  async getCalendarEvents() {
    return this.request<any[]>("/api/v1/calendar");
  }

  async createCalendarEvent(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/calendar", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getCalendarEvent(id: string) {
    return this.request<any>(`/api/v1/calendar/${id}`);
  }

  async updateCalendarEvent(id: string, data: Record<string, unknown>) {
    return this.request<any>(`/api/v1/calendar/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteCalendarEvent(id: string) {
    return this.request<any>(`/api/v1/calendar/${id}`, {
      method: "DELETE",
    });
  }

  // Audio (TTS)
  async getAudioConfig() {
    return this.request<any>("/api/v1/audio/config");
  }

  async configureAudio(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/audio/config", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async synthesizeAudio(data: { text: string; config?: Record<string, unknown> }) {
    return this.request<{ format: string; content_base64: string }>("/api/v1/audio/synthesize", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Images
  async getImagesConfig() {
    return this.request<any>("/api/v1/images/config");
  }

  async configureImages(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/images/config", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async generateImage(data: { prompt: string; config?: Record<string, unknown> }) {
    return this.request<{ format: string; content_base64: string }>("/api/v1/images/generate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Evaluations
  async getEvaluations() {
    return this.request<any[]>("/api/v1/evaluations");
  }

  async createEvaluation(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/evaluations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getEvaluation(id: string) {
    return this.request<any>(`/api/v1/evaluations/${id}`);
  }

  async addEvaluationResult(id: string, data: Record<string, unknown>) {
    return this.request<any>(`/api/v1/evaluations/${id}/results`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Analytics
  async recordAnalyticsEvent(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/analytics/events", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getAnalyticsEvents(params?: { event_type?: string; user_id?: string; limit?: number }) {
    const qs = new URLSearchParams();
    if (params?.event_type) qs.set("event_type", params.event_type);
    if (params?.user_id) qs.set("user_id", params.user_id);
    if (params?.limit !== undefined) qs.set("limit", String(params.limit));
    const suffix = qs.toString() ? `?${qs}` : "";
    return this.request<any[]>(`/api/v1/analytics/events${suffix}`);
  }

  async getAnalyticsSummary(userId?: string) {
    const qs = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return this.request<any>(`/api/v1/analytics/summary${qs}`);
  }

  // Channels
  async getChannels() {
    return this.request<any[]>("/api/v1/channels");
  }

  async createChannel(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/channels", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getChannel(id: string) {
    return this.request<any>(`/api/v1/channels/${id}`);
  }

  async updateChannel(id: string, data: Record<string, unknown>) {
    return this.request<any>(`/api/v1/channels/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteChannel(id: string) {
    return this.request<any>(`/api/v1/channels/${id}`, {
      method: "DELETE",
    });
  }

  async getChannelMessages(channelId: string) {
    return this.request<any[]>(`/api/v1/channels/${channelId}/messages`);
  }

  async addChannelMessage(channelId: string, data: Record<string, unknown>) {
    return this.request<any>(`/api/v1/channels/${channelId}/messages`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Notes
  async getNotes(params?: { user_id?: string; pinned?: boolean }) {
    const qs = new URLSearchParams();
    if (params?.user_id) qs.set("user_id", params.user_id);
    if (params?.pinned !== undefined) qs.set("pinned", String(params.pinned));
    const suffix = qs.toString() ? `?${qs}` : "";
    return this.request<any[]>(`/api/v1/notes${suffix}`);
  }

  async createNote(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/notes", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async searchNotes(q: string, userId?: string) {
    const qs = new URLSearchParams({ q });
    if (userId) qs.set("user_id", userId);
    return this.request<any[]>(`/api/v1/notes/search?${qs}`);
  }

  async getNote(id: string) {
    return this.request<any>(`/api/v1/notes/${id}`);
  }

  async updateNote(id: string, data: Record<string, unknown>) {
    return this.request<any>(`/api/v1/notes/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteNote(id: string) {
    return this.request<any>(`/api/v1/notes/${id}`, {
      method: "DELETE",
    });
  }

  // Tool servers
  async getToolServers(enabled?: boolean) {
    const qs = enabled !== undefined ? `?enabled=${enabled}` : "";
    return this.request<any[]>(`/api/v1/tools/servers${qs}`);
  }

  async registerToolServer(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/tools/servers", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getToolServer(id: string) {
    return this.request<any>(`/api/v1/tools/servers/${id}`);
  }

  async updateToolServer(id: string, data: Record<string, unknown>) {
    return this.request<any>(`/api/v1/tools/servers/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async setToolServerStatus(id: string, status: string) {
    return this.request<any>(`/api/v1/tools/servers/${id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    });
  }

  async deleteToolServer(id: string) {
    return this.request<any>(`/api/v1/tools/servers/${id}`, {
      method: "DELETE",
    });
  }

  // Functions & Pipelines
  async getFunctions() {
    return this.request<any[]>("/api/v1/functions");
  }

  async createFunction(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/functions", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getFunction(id: string) {
    return this.request<any>(`/api/v1/functions/${id}`);
  }

  async deleteFunction(id: string) {
    return this.request<any>(`/api/v1/functions/${id}`, {
      method: "DELETE",
    });
  }

  async getPipelines() {
    return this.request<any[]>("/api/v1/pipelines");
  }

  async createPipeline(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/pipelines", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getPipeline(id: string) {
    return this.request<any>(`/api/v1/pipelines/${id}`);
  }

  async deletePipeline(id: string) {
    return this.request<any>(`/api/v1/pipelines/${id}`, {
      method: "DELETE",
    });
  }

  // Prompts
  async getPrompts() {
    return this.request<any[]>("/api/v1/prompts");
  }

  async createPrompt(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/prompts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getPrompt(id: string) {
    return this.request<any>(`/api/v1/prompts/${id}`);
  }

  async updatePrompt(id: string, data: Record<string, unknown>) {
    return this.request<any>(`/api/v1/prompts/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deletePrompt(id: string) {
    return this.request<any>(`/api/v1/prompts/${id}`, {
      method: "DELETE",
    });
  }

  // SCIM
  async getScimConfig() {
    return this.request<any>("/api/v1/scim/config");
  }

  async configureScim(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/scim/config", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getScimStatus() {
    return this.request<{ enabled: boolean }>("/api/v1/scim/status");
  }
}

// Export singleton instance
export const apiClient = new ApiClient(API_BASE_URL);

// Export individual service modules for better organization
export const authService = {
  login: (email: string, password: string) => apiClient.login(email, password),
  logout: () => apiClient.logout(),
  refreshToken: () => apiClient.refreshToken(),
  getCurrentUser: () => apiClient.getCurrentUser(),
};

export const agentsService = {
  getAll: () => apiClient.getAgents(),
  getById: (id: string) => apiClient.getAgent(id),
  create: (data: { name: string; capabilities?: string[] }) =>
    apiClient.createAgent(data),
  update: (id: string, data: any) => apiClient.updateAgent(id, data),
  delete: (id: string) => apiClient.deleteAgent(id),
};

export const goalsService = {
  getAll: () => apiClient.getGoals(),
  getById: (id: string) => apiClient.getGoal(id),
  create: (data: { title: string; description?: string; priority?: string }) =>
    apiClient.createGoal(data),
  update: (id: string, data: any) => apiClient.updateGoal(id, data),
  delete: (id: string) => apiClient.deleteGoal(id),
};

export const memoryService = {
  search: (query: string, filters?: any) => apiClient.searchMemory(query, filters),
  store: (entry: any) => apiClient.storeMemory(entry),
  getById: (id: string) => apiClient.getMemoryEntry(id),
};

export const ragService = {
  getDocuments: () => apiClient.getRagDocuments(),
  ingestDocument: (data: {
    title?: string;
    source?: string;
    content: string;
    metadata?: Record<string, unknown>;
  }) => apiClient.ingestRagDocument(data),
};

export const skillsService = {
  getAll: () => apiClient.getSkills(),
  getById: (id: string) => apiClient.getSkill(id),
  execute: (id: string, params: any) => apiClient.executeSkill(id, params),
};

export const fluxService = {
  getEvents: (filters?: any) => apiClient.getFluxEvents(filters),
};

export const settingsService = {
  get: () => apiClient.getSettings(),
  update: (data: any) => apiClient.updateSettings(data),
};

export const automationsService = {
  getAll: (enabled?: boolean) => apiClient.getAutomations(enabled),
  getById: (id: string) => apiClient.getAutomation(id),
  create: (data: Record<string, unknown>) => apiClient.createAutomation(data),
  update: (id: string, data: Record<string, unknown>) => apiClient.updateAutomation(id, data),
  delete: (id: string) => apiClient.deleteAutomation(id),
  trigger: (id: string) => apiClient.triggerAutomation(id),
};

export const calendarService = {
  getAll: () => apiClient.getCalendarEvents(),
  getById: (id: string) => apiClient.getCalendarEvent(id),
  create: (data: Record<string, unknown>) => apiClient.createCalendarEvent(data),
  update: (id: string, data: Record<string, unknown>) => apiClient.updateCalendarEvent(id, data),
  delete: (id: string) => apiClient.deleteCalendarEvent(id),
};

export const audioService = {
  getConfig: () => apiClient.getAudioConfig(),
  configure: (data: Record<string, unknown>) => apiClient.configureAudio(data),
  synthesize: (data: { text: string; config?: Record<string, unknown> }) =>
    apiClient.synthesizeAudio(data),
};

export const imagesService = {
  getConfig: () => apiClient.getImagesConfig(),
  configure: (data: Record<string, unknown>) => apiClient.configureImages(data),
  generate: (data: { prompt: string; config?: Record<string, unknown> }) =>
    apiClient.generateImage(data),
};

export const evaluationsService = {
  getAll: () => apiClient.getEvaluations(),
  getById: (id: string) => apiClient.getEvaluation(id),
  create: (data: Record<string, unknown>) => apiClient.createEvaluation(data),
  addResult: (id: string, data: Record<string, unknown>) =>
    apiClient.addEvaluationResult(id, data),
};

export const analyticsService = {
  recordEvent: (data: Record<string, unknown>) => apiClient.recordAnalyticsEvent(data),
  getEvents: (params?: { event_type?: string; user_id?: string; limit?: number }) =>
    apiClient.getAnalyticsEvents(params),
  getSummary: (userId?: string) => apiClient.getAnalyticsSummary(userId),
};

export const channelsService = {
  getAll: () => apiClient.getChannels(),
  getById: (id: string) => apiClient.getChannel(id),
  create: (data: Record<string, unknown>) => apiClient.createChannel(data),
  update: (id: string, data: Record<string, unknown>) => apiClient.updateChannel(id, data),
  delete: (id: string) => apiClient.deleteChannel(id),
  getMessages: (channelId: string) => apiClient.getChannelMessages(channelId),
  addMessage: (channelId: string, data: Record<string, unknown>) =>
    apiClient.addChannelMessage(channelId, data),
};

export const notesService = {
  getAll: (params?: { user_id?: string; pinned?: boolean }) => apiClient.getNotes(params),
  getById: (id: string) => apiClient.getNote(id),
  create: (data: Record<string, unknown>) => apiClient.createNote(data),
  update: (id: string, data: Record<string, unknown>) => apiClient.updateNote(id, data),
  delete: (id: string) => apiClient.deleteNote(id),
  search: (q: string, userId?: string) => apiClient.searchNotes(q, userId),
};

export const toolServersService = {
  getAll: (enabled?: boolean) => apiClient.getToolServers(enabled),
  getById: (id: string) => apiClient.getToolServer(id),
  register: (data: Record<string, unknown>) => apiClient.registerToolServer(data),
  update: (id: string, data: Record<string, unknown>) => apiClient.updateToolServer(id, data),
  setStatus: (id: string, status: string) => apiClient.setToolServerStatus(id, status),
  delete: (id: string) => apiClient.deleteToolServer(id),
};

export const functionsService = {
  getAll: () => apiClient.getFunctions(),
  getById: (id: string) => apiClient.getFunction(id),
  create: (data: Record<string, unknown>) => apiClient.createFunction(data),
  delete: (id: string) => apiClient.deleteFunction(id),
  getPipelines: () => apiClient.getPipelines(),
  getPipeline: (id: string) => apiClient.getPipeline(id),
  createPipeline: (data: Record<string, unknown>) => apiClient.createPipeline(data),
  deletePipeline: (id: string) => apiClient.deletePipeline(id),
};

export const promptsService = {
  getAll: () => apiClient.getPrompts(),
  getById: (id: string) => apiClient.getPrompt(id),
  create: (data: Record<string, unknown>) => apiClient.createPrompt(data),
  update: (id: string, data: Record<string, unknown>) => apiClient.updatePrompt(id, data),
  delete: (id: string) => apiClient.deletePrompt(id),
};

export const scimService = {
  getConfig: () => apiClient.getScimConfig(),
  configure: (data: Record<string, unknown>) => apiClient.configureScim(data),
  getStatus: () => apiClient.getScimStatus(),
};

export type { HealthStatus, SystemMetrics } from "./types";
