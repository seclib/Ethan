"use client";

/**
 * useProviders — Gestion complète des providers LLM.
 *
 * Fournit :
 * - La liste des providers (avec état enabled/status)
 * - CRUD + activation/désactivation via le ProviderManager Core
 * - Test de connexion en temps réel (healthcheck)
 * - Définition du provider par défaut
 * - États de chargement/mutation (via TanStack Query)
 *
 * Ne gère AUCUNE logique métier : tout est délégué au ProviderManager Core.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
	listProviders,
	getProvider,
	createProvider,
	updateProvider,
	deleteProvider,
	testProviderConnection,
	setDefaultProvider,
	listProviderModels,
	type Provider,
	type ProviderCreate,
	type ProviderUpdate,
	type TestConnectionResult,
} from "@/lib/api/providers";
import { useUIStore } from "@/store/ui.store";

const QUERY_KEY = "providers";

export function useProviders() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	const { data: providers = [], isLoading, error, refetch } = useQuery<Provider[]>({
		queryKey: [QUERY_KEY],
		queryFn: listProviders,
		staleTime: 15_000,
		retry: 1,
	});

	const invalidate = () => queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });

	// ── Mutations ─────────────────────────────────────────────
	const createMutation = useMutation({
		mutationFn: createProvider,
		onSuccess: (data) => {
			invalidate();
			addToast({ type: "success", message: `Provider "${data?.name}" created` });
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: `Failed to create provider: ${err.message}` });
		},
	});

	const updateMutation = useMutation({
		mutationFn: ({ id, data }: { id: string; data: ProviderUpdate }) => updateProvider(id, data),
		onSuccess: (data) => {
			invalidate();
			addToast({ type: "success", message: `Provider "${data?.name}" updated` });
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: `Failed to update provider: ${err.message}` });
		},
	});

	const deleteMutation = useMutation({
		mutationFn: deleteProvider,
		onSuccess: (data) => {
			invalidate();
			addToast({ type: "success", message: `Provider deleted` });
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: `Failed to delete provider: ${err.message}` });
		},
	});

	const testMutation = useMutation({
		mutationFn: testProviderConnection,
		onSuccess: (data: TestConnectionResult) => {
			if (data.connected) {
				addToast({ type: "success", message: `Provider "${data.provider_id}" is reachable` });
			} else {
				addToast({ type: "warning", message: `Provider "${data.provider_id}": ${data.message}` });
			}
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: `Test failed: ${err.message}` });
		},
	});

	const setEnabledMutation = useMutation({
		mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
			updateProvider(id, { enabled }),
		onSuccess: () => invalidate(),
	});

	const setDefaultMutation = useMutation({
		mutationFn: setDefaultProvider,
		onSuccess: (data) => {
			invalidate();
			addToast({ type: "success", message: `Default provider set` });
		},
		onError: (err: Error) => {
			addToast({ type: "error", message: `Failed: ${err.message}` });
		},
	});

	// ── Actions exposées ─────────────────────────────────────
	return {
		providers,
		isLoading,
		error: error instanceof Error ? error.message : null,
		refetch,
		isCreating: createMutation.isPending,
		isUpdating: updateMutation.isPending,
		isDeleting: deleteMutation.isPending,
		isTesting: testMutation.isPending,

		// CRUD
		createProviderAsync: async (data: ProviderCreate) => {
			const result = await createMutation.mutateAsync(data);
			return result;
		},
		updateProviderAsync: async (id: string, data: ProviderUpdate) => {
			const result = await updateMutation.mutateAsync({ id, data });
			return result;
		},
		deleteProviderAsync: async (id: string) => {
			const result = await deleteMutation.mutateAsync(id);
			return result;
		},

		// Toggles
		async toggleEnabled(id: string, enabled: boolean) {
			await setEnabledMutation.mutateAsync({ id, enabled });
		},

		// Test
		async testConnection(id: string) {
			const result = await testMutation.mutateAsync(id);
			return result;
		},

		// Default
		async setDefault(id: string) {
			const result = await setDefaultMutation.mutateAsync(id);
			return result;
		},

		// Provider-specific models
		async fetchModels(id: string) {
			return listProviderModels(id);
		},

		// Helpers
		getProvider: (id: string) => providers.find((p) => p.id === id),
		enabledProviders: providers.filter((p) => p.enabled),
		disabledProviders: providers.filter((p) => !p.enabled),
	};
}
