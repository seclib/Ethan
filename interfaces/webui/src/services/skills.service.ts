import { apiClient } from "./api-client";
import type { Skill, ApiResponse } from "@/types";

export const skillsService = {
  getAll: () =>
    apiClient.request<ApiResponse<Skill[]>>("/api/v1/skills"),

  getById: (id: string) =>
    apiClient.request<ApiResponse<Skill>>(`/api/v1/skills/${id}`),

  create: (data: { name: string; description: string }) =>
    apiClient.request<ApiResponse<Skill>>("/api/v1/skills", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<Skill>) =>
    apiClient.request<ApiResponse<Skill>>(`/api/v1/skills/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiClient.request<void>(`/api/v1/skills/${id}`, {
      method: "DELETE",
    }),

  test: (id: string) =>
    apiClient.request<ApiResponse<{ passed: boolean; output: string }>>(
      `/api/v1/skills/${id}/test`,
      { method: "POST" }
    ),

  install: (id: string) =>
    apiClient.request<ApiResponse<Skill>>(`/api/v1/skills/${id}/install`, {
      method: "POST",
    }),
};