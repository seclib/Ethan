"use client";

import { useQuery } from "@tanstack/react-query";
import { listFluxEvents, getFluxEvent } from "@/lib/api/flux";
import type { FluxEvent } from "@/types";

export function useFluxEvents(limit?: number, type?: string) {
	const { data, isLoading, error, refetch } = useQuery<FluxEvent[]>({
		queryKey: ["fluxEvents", limit, type],
		queryFn: () => listFluxEvents(limit, type),
	});

	return {
		events: data || [],
		isLoading,
		error: error instanceof Error ? error.message : null,
		refetch,
	};
}

export function useFluxEvent(id: string | null) {
	const { data, isLoading, error } = useQuery<FluxEvent | null>({
		queryKey: ["fluxEvent", id],
		queryFn: () => (id ? getFluxEvent(id) : null),
		enabled: !!id,
	});

	return {
		event: data || null,
		isLoading,
		error: error instanceof Error ? error.message : null,
	};
}
