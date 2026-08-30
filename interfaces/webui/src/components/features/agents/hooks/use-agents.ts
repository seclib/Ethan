"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listAgents, getAgent, createAgent, updateAgent, deleteAgent, executeAgent } from "@/lib/api/agents";
import { useUIStore } from "@/store/ui.store";
import type { Agent } from "@/types";

export function useAgents() {
	const { data: agents = [], isLoading, error, refetch } = useQuery<Agent[]>({
		queryKey: ["agents"],
		queryFn: () => listAgents(),
	});

	return {
		agents,
		isLoading,
		error: error instanceof Error ? error.message : null,
		refetch,
	};
}

export function useExecuteAgent() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);
	const mutation = useMutation({
		mutationFn: ({
			id,
			task,
			context,
			skill_id,
		}: {
			id: string;
			task: string;
			context?: Record<string, unknown>;
			skill_id?: string;
		}) => executeAgent(id, { task, context, skill_id }),
		onSuccess: (execution) => {
			queryClient.invalidateQueries({ queryKey: ["agents"] });
			if (execution.status === "failed") {
				addToast({ type: "error", message: execution.error || "L'exécution de l'agent a échoué" });
			} else {
				addToast({ type: "success", message: `Agent exécuté (${execution.status})` });
			}
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: err.message || "Failed to execute agent" });
		},
	});

	return {
		mutate: async (params: { id: string; task: string; context?: Record<string, unknown>; skill_id?: string }) => {
			try {
				const result = await mutation.mutateAsync(params);
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed to execute agent" };
			}
		},
		isLoading: mutation.isPending,
	};
}

export function useAgent(id: string | null) {
	const { data: agent, isLoading, error } = useQuery<Agent | null>({
		queryKey: ["agents", id],
		queryFn: () => (id ? getAgent(id) : null),
		enabled: !!id,
	});

	return {
		agent: agent || null,
		isLoading,
		error: error instanceof Error ? error.message : null,
	};
}

export function useCreateAgent() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);
	const mutation = useMutation({
		mutationFn: (data: {
			name: string;
			description?: string;
			capabilities?: string[];
			model?: string;
			provider?: string;
			skill_ids?: string[];
			metadata?: Record<string, unknown>;
		}) => createAgent(data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["agents"] });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to create agent" });
		},
	});

	return {
		mutate: async (data: {
			name: string;
			description?: string;
			capabilities?: string[];
			model?: string;
			provider?: string;
			skill_ids?: string[];
			metadata?: Record<string, unknown>;
		}) => {
			try {
				const result = await mutation.mutateAsync(data);
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed to create agent" };
			}
		},
		isLoading: mutation.isPending,
	};
}

export function useUpdateAgent() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);
	const mutation = useMutation({
		mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
			updateAgent(id, data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["agents"] });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to update agent" });
		},
	});

	return {
		mutate: async (id: string, data: Record<string, unknown>) => {
			try {
				const result = await mutation.mutateAsync({ id, data });
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed to update agent" };
			}
		},
		isLoading: mutation.isPending,
	};
}

export function useDeleteAgent() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);
	const mutation = useMutation({
		mutationFn: (id: string) => deleteAgent(id),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["agents"] });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to delete agent" });
		},
	});

	return {
		mutate: async (id: string) => {
			try {
				await mutation.mutateAsync(id);
				return { error: null };
			} catch (err) {
				return { error: err instanceof Error ? err.message : "Failed to delete agent" };
			}
		},
		isLoading: mutation.isPending,
	};
}