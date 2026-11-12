"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listMissions, getMission, createMission, deleteMission, verifyMissionStep } from "@/lib/api/missions";
import type { Mission } from "@/lib/api/missions";

export function useMissions() {
	const queryClient = useQueryClient();

	const { data, isLoading, error, refetch } = useQuery<Mission[]>({
		queryKey: ["missions"],
		queryFn: () => listMissions(),
	});

	const createMutation = useMutation({
		mutationFn: (data: { title: string; description?: string }) => createMission(data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["missions"] });
		},
	});

	const deleteMutation = useMutation({
		mutationFn: (id: string) => deleteMission(id),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["missions"] });
		},
	});

	return {
		missions: data || [],
		isLoading,
		error: error instanceof Error ? error.message : null,
		refetch,
		create: (data: { title: string; description?: string }) => createMutation.mutateAsync(data),
		deletes: (id: string) => deleteMutation.mutateAsync(id),
	};
}

export function useMission(id: string | null) {
	const { data, isLoading, error } = useQuery<Mission | null>({
		queryKey: ["missions", id],
		queryFn: () => (id ? getMission(id) : null),
		enabled: !!id,
	});

	return {
		mission: data || null,
		isLoading,
		error: error instanceof Error ? error.message : null,
	};
}

export function useCreateMission() {
	const queryClient = useQueryClient();
	const mutation = useMutation({
		mutationFn: (data: { title: string; description?: string }) => createMission(data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["missions"] });
		},
	});

	return {
		mutate: async (data: { title: string; description?: string }) => {
			try {
				const result = await mutation.mutateAsync(data);
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed to create mission" };
			}
		},
		isLoading: mutation.isPending,
	};
}

export function useVerifyStep() {
	const queryClient = useQueryClient();
	const mutation = useMutation({
		mutationFn: ({ missionId, stepId }: { missionId: string; stepId: string }) =>
			verifyMissionStep(missionId, stepId),
		onSuccess: (_, variables) => {
			queryClient.invalidateQueries({ queryKey: ["missions"] });
			queryClient.invalidateQueries({ queryKey: ["missions", variables.missionId] });
		},
	});

	return {
		mutate: async (missionId: string, stepId: string) => {
			try {
				const result = await mutation.mutateAsync({ missionId, stepId });
				return { verified: Boolean((result as { verified?: boolean })?.verified), error: null };
			} catch (err) {
				return { verified: false, error: err instanceof Error ? err.message : "Failed to verify step" };
			}
		},
		isLoading: mutation.isPending,
	};
}