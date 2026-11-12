"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listGoals, getGoal, createGoal, updateGoal, deleteGoal } from "@/lib/api/goals";
import { useUIStore } from "@/store/ui.store";
import type { Goal } from "@/types";

export function useGoals() {
	const { data: goals = [], isLoading, error, refetch } = useQuery<Goal[]>({
		queryKey: ["goals"],
		queryFn: () => listGoals(),
	});

	return {
		goals,
		isLoading,
		error: error instanceof Error ? error.message : null,
		refetch,
	};
}

export function useGoal(id: string | null) {
	const { data: goal, isLoading, error } = useQuery<Goal | null>({
		queryKey: ["goals", id],
		queryFn: () => (id ? getGoal(id) : null),
		enabled: !!id,
	});

	return {
		goal: goal || null,
		isLoading,
		error: error instanceof Error ? error.message : null,
	};
}

export function useCreateGoal() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);
	const mutation = useMutation({
		mutationFn: (data: { title: string; description?: string; priority?: string }) =>
			createGoal(data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["goals"] });
			addToast({ type: "success", message: "Goal created" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to create goal" });
		},
	});

	return {
		mutate: async (data: { title: string; description?: string; priority?: string }) => {
			try {
				const result = await mutation.mutateAsync(data);
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed to create goal" };
			}
		},
		isLoading: mutation.isPending,
	};
}

export function useUpdateGoal() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);
	const mutation = useMutation({
		mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
			updateGoal(id, data),
		onSuccess: (_, { id }) => {
			queryClient.invalidateQueries({ queryKey: ["goals"] });
			queryClient.invalidateQueries({ queryKey: ["goals", id] });
			addToast({ type: "success", message: "Goal updated" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to update goal" });
		},
	});

	return {
		mutate: async (id: string, data: Record<string, unknown>) => {
			try {
				const result = await mutation.mutateAsync({ id, data });
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed to update goal" };
			}
		},
		isLoading: mutation.isPending,
	};
}

export function useDeleteGoal() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);
	const mutation = useMutation({
		mutationFn: (id: string) => deleteGoal(id),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["goals"] });
			addToast({ type: "success", message: "Goal deleted" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to delete goal" });
		},
	});

	return {
		mutate: async (id: string) => {
			try {
				await mutation.mutateAsync(id);
				return { error: null };
			} catch (err) {
				return { error: err instanceof Error ? err.message : "Failed to delete goal" };
			}
		},
		isLoading: mutation.isPending,
	};
}