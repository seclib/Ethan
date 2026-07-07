import { apiClient } from "./api-client";
import type { Fact, MemoryEvent, ApiResponse } from "@/types";

export const memoryService = {
  getAll: () =>
    apiClient.request<ApiResponse<MemoryEvent[]>>("/api/v1/memory/events"),

  getFacts: (filters?: Record<string, string>) => {
    const params = filters ? new URLSearchParams(filters).toString() : "";
    return apiClient.request<ApiResponse<Fact[]>>(`/api/v1/memory/facts?${params}`);
  },

  search: (query: string, filters?: Record<string, string>) => {
    const params = new URLSearchParams({ query, ...filters }).toString();
    return apiClient.request<ApiResponse<Fact[]>>(`/api/v1/memory/search?${params}`);
  },

  store: (entry: any) =>
    apiClient.request<ApiResponse<MemoryEvent>>("/api/v1/memory/ingest", {
      method: "POST",
      body: JSON.stringify(entry),
    }),

  getById: (id: string) =>
    apiClient.request<ApiResponse<MemoryEvent>>(`/api/v1/memory/${id}`),

  getFactById: (id: string) =>
    apiClient.request<ApiResponse<Fact>>(`/api/v1/memory/facts/${id}`),
};