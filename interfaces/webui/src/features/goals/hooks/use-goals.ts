"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { goalsService } from "@/core/api/api-client";
import type { Goal } from "@/types";

export function useGoals() {
  const { data: goals = [], isLoading, error, refetch } = useQuery<Goal[]>({
    queryKey: ["goals"],
    queryFn: () => goalsService.getAll(),
  });

  return {
    goals,
    isLoading,
    error: error instanceof Error ? error.message : null,
    refetch,
    clearError: () => {}, 
  };
}

export function useGoal(id: string | null) {
  const { data: goal = null, isLoading, error } = useQuery<Goal | null>({
    queryKey: ["goals", id],
    queryFn: () => id ? goalsService.getById(id) : null,
    enabled: !!id,
  });

  return {
    goal,
    isLoading,
    error: error instanceof Error ? error.message : null,
    clearError: () => {},
  };
}

export function useCreateGoal() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (data: { title: string; description?: string; priority?: string }) => goalsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });

  return {
    mutate: async (data: { title: string; description?: string; priority?: string }) => {
      try {
        const result = await mutation.mutateAsync(data);
        return { data: result, error: null };
      } catch (error) {
        return { data: null, error: error instanceof Error ? error.message : "Failed to create goal" };
      }
    },
    isLoading: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
    clearError: mutation.reset,
  };
}

export function useUpdateGoal() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Goal> }) => goalsService.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["goals", variables.id] });
    },
  });

  return {
    mutate: async (id: string, data: Partial<Goal>) => {
      try {
        const result = await mutation.mutateAsync({ id, data });
        return { data: result, error: null };
      } catch (error) {
        return { data: null, error: error instanceof Error ? error.message : "Failed to update goal" };
      }
    },
    isLoading: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
    clearError: mutation.reset,
  };
}

export function useDeleteGoal() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (id: string) => goalsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });

  return {
    mutate: async (id: string) => {
      try {
        await mutation.mutateAsync(id);
        return { error: null };
      } catch (error) {
        return { error: error instanceof Error ? error.message : "Failed to delete goal" };
      }
    },
    isLoading: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
    clearError: mutation.reset,
  };
}