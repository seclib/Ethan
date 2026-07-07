/**
 * Centralized API client with interceptors
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.loadToken();
  }

  private loadToken() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("ethan_token");
    }
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

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 Unauthorized
      if (response.status === 401) {
        this.token = null;
        if (typeof window !== "undefined") {
          localStorage.removeItem("ethan_token");
        }
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
    return this.request<{ token: string; user: any }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async logout() {
    return this.request<void>("/api/v1/auth/logout", {
      method: "POST",
    });
  }

  async refreshToken() {
    return this.request<{ token: string }>("/api/v1/auth/refresh", {
      method: "POST",
    });
  }

  async getCurrentUser() {
    return this.request<any>("/api/v1/auth/me");
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
    return this.request<any>("/api/v1/memory/store", {
      method: "POST",
      body: JSON.stringify(entry),
    });
  }

  async getMemoryEntry(id: string) {
    return this.request<any>(`/api/v1/memory/${id}`);
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