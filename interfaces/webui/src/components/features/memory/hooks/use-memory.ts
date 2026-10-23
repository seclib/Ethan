"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listFacts, searchFacts, deleteFact, listMemoryEvents, ingestMemory } from "@/lib/api/memory";
import { useUIStore } from "@/store/ui.store";
import type { Fact, MemoryEvent } from "@/types";

export function useFacts(filters?: { query?: string; category?: string; limit?: number }) {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	const { data, isLoading, error, refetch } = useQuery<Fact[]>({
		queryKey: ["facts", filters],
		queryFn: () => {
			if (filters?.query) {
				return searchFacts(filters.query);
			}
			return listFacts(filters?.limit, filters?.category);
		},
	});

	const deleteMutation = useMutation({
		mutationFn: (id: string) => deleteFact(id),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["facts"] });
			addToast({ type: "success", message: "Fact deleted" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to delete fact" });
		},
	});

	return {
		facts: data || [],
		isLoading,
		error: error instanceof Error ? error.message : null,
		fetchFacts: refetch,
		deleteFact: async (id: string) => {
			try {
				const result = await deleteMutation.mutateAsync(id);
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed to delete fact" };
			}
		},
		isDeleting: deleteMutation.isPending,
	};
}

export function useMemoryEvents() {
	const { data, isLoading, error, refetch } = useQuery<MemoryEvent[]>({
		queryKey: ["memoryEvents"],
		queryFn: () => listMemoryEvents(),
	});

	return {
		events: data || [],
		isLoading,
		error: error instanceof Error ? error.message : null,
		fetchEvents: refetch,
	};
}

export function useStoreMemory() {
	const queryClient = useQueryClient();
	const mutation = useMutation({
		mutationFn: (entry: Record<string, unknown>) => ingestMemory(entry),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["memoryEvents"] });
			queryClient.invalidateQueries({ queryKey: ["facts"] });
		},
	});

	return {
		mutate: async (entry: Record<string, unknown>) => {
			try {
				const result = await mutation.mutateAsync(entry);
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed to store memory" };
			}
		},
		isLoading: mutation.isPending,
	};
}