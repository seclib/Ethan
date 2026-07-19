import { apiClient } from "@/core/api/api-client";

export const pluginsService = {
  getAll: () => apiClient.request("/api/v1/plugins"),
  getById: (id: string) => apiClient.request(`/api/v1/plugins/${id}`),
  install: (name: string, source: string) =>
    apiClient.request("/api/v1/plugins/install", {
      method: "POST",
      body: JSON.stringify({ name, source }),
    }),
  uninstall: (id: string) =>
    apiClient.request(`/api/v1/plugins/${id}`, { method: "DELETE" }),
  toggle: (id: string, enabled: boolean) =>
    apiClient.request(`/api/v1/plugins/${id}/toggle`, {
      method: "PUT",
      body: JSON.stringify({ enabled }),
    }),
};