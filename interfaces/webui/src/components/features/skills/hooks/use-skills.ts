"use client";

/**
 * useSkills — Gestion des skills Core.
 *
 * Couvre : list, search, create, update, delete, toggle (enable/disable) et
 * execute. SkillStore est Core-owned ; la WebUI ne fait que déclencher.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
	listSkills,
	createSkill as apiCreateSkill,
	updateSkill as apiUpdateSkill,
	deleteSkill as apiDeleteSkill,
	toggleSkill as apiToggleSkill,
	executeSkill as apiExecuteSkill,
	searchSkills,
	type Skill,
} from "@/lib/api/skills";
import { useUIStore } from "@/store/ui.store";
import { useState } from "react";

export function useSkills() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	const { data: skills = [], isLoading, error, refetch } = useQuery<Skill[]>({
		queryKey: ["skills"],
		queryFn: () => listSkills(),
		staleTime: 15_000,
	});

	const invalidate = () => queryClient.invalidateQueries({ queryKey: ["skills"] });

	const createMutation = useMutation({
		mutationFn: (data: {
			name: string;
			description?: string;
			content?: string;
			version?: string;
			tags?: string[];
			meta?: Record<string, unknown>;
		}) => apiCreateSkill(data),
		onSuccess: (data) => {
			invalidate();
			addToast({ type: "success", message: `Skill "${data?.name}" créé` });
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: err.message || "Échec de création du skill" });
		},
	});

	const updateMutation = useMutation({
		mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
			apiUpdateSkill(id, data),
		onSuccess: () => {
			invalidate();
			addToast({ type: "success", message: "Skill mis à jour" });
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: err.message || "Échec de mise à jour" });
		},
	});

	const deleteMutation = useMutation({
		mutationFn: (id: string) => apiDeleteSkill(id),
		onSuccess: () => {
			invalidate();
			addToast({ type: "success", message: "Skill supprimé" });
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: err.message || "Échec de suppression" });
		},
	});

	const toggleMutation = useMutation({
		mutationFn: (id: string) => apiToggleSkill(id),
		onSuccess: () => invalidate(),
		onError: (err: Error) => {
			addToast({ type: "error", message: err.message || "Échec du toggle" });
		},
	});

	const executeMutation = useMutation({
		mutationFn: ({ id, params }: { id: string; params: Record<string, unknown> }) =>
			apiExecuteSkill(id, params),
		onSuccess: (result) => {
			addToast({ type: "success", message: `Skill exécuté (${result.status})` });
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: err.message || "Échec d'exécution" });
		},
	});

	return {
		skills,
		isLoading,
		error: error instanceof Error ? error.message : null,
		refetch,
		search: async (q: string) => searchSkills(q),
		createSkill: async (data: { name: string; description?: string; content?: string; version?: string; tags?: string[]; meta?: Record<string, unknown> }) => {
			try {
				const result = await createMutation.mutateAsync(data);
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed" };
			}
		},
		updateSkill: async (id: string, data: Record<string, unknown>) => {
			try {
				const result = await updateMutation.mutateAsync({ id, data });
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed" };
			}
		},
		deleteSkill: async (id: string) => {
			try {
				await deleteMutation.mutateAsync(id);
				return { error: null };
			} catch (err) {
				return { error: err instanceof Error ? err.message : "Failed" };
			}
		},
		toggleSkill: async (id: string) => {
			try {
				await toggleMutation.mutateAsync(id);
				return { error: null };
			} catch (err) {
				return { error: err instanceof Error ? err.message : "Failed" };
			}
		},
		executeSkill: async (id: string, params: Record<string, unknown> = {}) => {
			try {
				const result = await executeMutation.mutateAsync({ id, params });
				return { data: result, error: null };
			} catch (err) {
				return { data: null, error: err instanceof Error ? err.message : "Failed" };
			}
		},
		isCreating: createMutation.isPending,
		isExecuting: executeMutation.isPending,
	};
}