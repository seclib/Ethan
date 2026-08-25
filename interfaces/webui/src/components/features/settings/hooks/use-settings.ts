"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSettings, updateSettings } from "@/lib/api/settings";
import { useUIStore } from "@/store/ui.store";
import type { Settings } from "@/types";

export function useSettings() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	const { data: settings, isLoading, error, refetch } = useQuery<Settings>({
		queryKey: ["settings"],
		queryFn: () => getSettings(),
	});

	const updateMutation = useMutation({
		mutationFn: (data: Partial<Settings>) => updateSettings(data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["settings"] });
			addToast({ type: "success", message: "Settings updated" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to update settings" });
		},
	});

	return {
		settings: settings || null,
		isLoading,
		error: error instanceof Error ? error.message : null,
		refetch,
		update: async (data: Partial<Settings>) => {
			try {
				const result = await updateMutation.mutateAsync(data);
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed to update settings" };
			}
		},
		isUpdating: updateMutation.isPending,
	};
}