import { apiClient } from "@/core/api/api-client";
import type { FluxEvent, ApiResponse } from "@/types";

export const fluxService = {
  getEvents: (filters?: Record<string, string>) => {
    const params = filters ? new URLSearchParams(filters).toString() : "";
    return apiClient.request<ApiResponse<FluxEvent[]>>(`/api/v1/flux?${params}`);
  },

  getEventById: (id: string) =>
    apiClient.request<ApiResponse<FluxEvent>>(`/api/v1/flux/${id}`),
};