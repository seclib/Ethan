import { apiClient } from "./api-client";
import type { Mission, ApiResponse } from "@/types";

export const missionsService = {
  getAll: () =>
    apiClient.request<ApiResponse<Mission[]>>("/api/v1/missions"),

  getById: (id: string) =>
    apiClient.request<ApiResponse<Mission>>(`/api/v1/missions/${id}`),

  create: (data: { title: string; description: string }) =>
    apiClient.request<ApiResponse<Mission>>("/api/v1/missions", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<Mission>) =>
    apiClient.request<ApiResponse<Mission>>(`/api/v1/missions/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiClient.request<void>(`/api/v1/missions/${id}`, {
      method: "DELETE",
    }),

  verifyStep: (missionId: string, stepId: string) =>
    apiClient.request<ApiResponse<{ verified: boolean }>>(
      `/api/v1/missions/${missionId}/steps/${stepId}/verify`,
      { method: "POST" }
    ),

  approveStep: (missionId: string, stepId: string) =>
    apiClient.request<ApiResponse<void>>(
      `/api/v1/missions/${missionId}/steps/${stepId}/approve`,
      { method: "POST" }
    ),
};