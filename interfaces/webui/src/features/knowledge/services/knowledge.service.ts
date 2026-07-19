import { apiClient } from "@/core/api/api-client";

export const knowledgeService = {
  getAll: () => apiClient.request("/api/v1/knowledge"),
  getById: (id: string) => apiClient.request(`/api/v1/knowledge/${id}`),
  search: (query: string) =>
    apiClient.request(`/api/v1/knowledge/search?q=${encodeURIComponent(query)}`),
};
