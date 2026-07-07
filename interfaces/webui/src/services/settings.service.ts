import { apiClient } from "./api-client";
import type { Settings, ApiResponse } from "@/types";

export const settingsService = {
  get: () =>
    apiClient.request<ApiResponse<Settings>>("/api/v1/settings"),

  update: (data: Partial<Settings>) =>
    apiClient.request<ApiResponse<Settings>>("/api/v1/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getLLM: () =>
    apiClient.request<ApiResponse<Settings["llm"]>>("/api/v1/settings/llm"),

  updateLLM: (data: Partial<Settings["llm"]>) =>
    apiClient.request<ApiResponse<Settings["llm"]>>("/api/v1/settings/llm", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getPermissions: () =>
    apiClient.request<ApiResponse<Settings["permissions"]>>("/api/v1/settings/permissions"),

  updatePermissions: (data: Partial<Settings["permissions"]>) =>
    apiClient.request<ApiResponse<Settings["permissions"]>>("/api/v1/settings/permissions", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getGovernance: () =>
    apiClient.request<ApiResponse<Settings["governance"]>>("/api/v1/settings/governance"),

  updateGovernance: (data: Partial<Settings["governance"]>) =>
    apiClient.request<ApiResponse<Settings["governance"]>>("/api/v1/settings/governance", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getBudget: () =>
    apiClient.request<ApiResponse<Settings["budget"]>>("/api/v1/settings/budget"),

  updateBudget: (data: Partial<Settings["budget"]>) =>
    apiClient.request<ApiResponse<Settings["budget"]>>("/api/v1/settings/budget", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};