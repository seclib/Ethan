"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { agentsService } from "@/core/api/api-client";
import { useUIStore } from "@/core/store/ui.store";
import type { Agent } from "@/types";

export function useAgents() {
  const { data: agents = [], isLoading, error, refetch } = useQuery<Agent[]>({
    queryKey: ["agents"],
    queryFn: () => agentsService.getAll(),
  });

  return {
    agents,
    isLoading,
    error: error instanceof Error ? error.message : null,
    refetch,
    clearError: () => {}, 
  };
}

export function useAgent(id: string | null) {
  const { data: agent = null, isLoading, error } = useQuery<Agent | null>({
    queryKey: ["agents", id],
    queryFn: () => id ? agentsService.getById(id) : null,
    enabled: !!id,
  });

  return {
    agent,
    isLoading,
    error: error instanceof Error ? error.message : null,
    clearError: () => {},
  };
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (data: { name: string; capabilities?: string[] }) => agentsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] });
      useUIStore.getState().addToast({
        type: "success",
        message: "Agent deployed successfully",
      });
    },
    onError: (err) => {
      useUIStore.getState().addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to deploy agent",
      });
    }
  });

  return {
    mutate: async (data: { name: string; capabilities?: string[] }) => {
      try {
        const result = await mutation.mutateAsync(data);
        return { data: result, error: null };
      } catch (error) {
        return { data: null, error: error instanceof Error ? error.message : "Failed to create agent" };
      }
    },
    isLoading: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
    clearError: mutation.reset,
  };
}

export function useUpdateAgent() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Agent> }) => agentsService.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["agents"] });
      queryClient.invalidateQueries({ queryKey: ["agents", variables.id] });
      useUIStore.getState().addToast({
        type: "success",
        message: "Agent parameters updated",
      });
    },
    onError: (err) => {
      useUIStore.getState().addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to update agent",
      });
    }
  });

  return {
    mutate: async (id: string, data: Partial<Agent>) => {
      try {
        const result = await mutation.mutateAsync({ id, data });
        return { data: result, error: null };
      } catch (error) {
        return { data: null, error: error instanceof Error ? error.message : "Failed to update agent" };
      }
    },
    isLoading: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
    clearError: mutation.reset,
  };
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (id: string) => agentsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    },
  });

  return {
    mutate: async (id: string) => {
      try {
        await mutation.mutateAsync(id);
        return { error: null };
      } catch (error) {
        return { error: error instanceof Error ? error.message : "Failed to delete agent" };
      }
    },
    isLoading: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
    clearError: mutation.reset,
  };
}