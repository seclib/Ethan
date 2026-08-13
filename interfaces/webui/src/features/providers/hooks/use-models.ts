"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api/api-client";
import { useUIStore } from "@/core/store/ui.store";
import type { Provider, ProviderModel } from "@/core/api/providers.types";

const STORAGE_PINNED = "ethan.pinned-models";

export interface PinnedModel {
  providerId: string;
  modelId: string;
  pinnedAt: string;
}

/**
 * Hook avancé pour la gestion des modèles.
 * - Recherche par nom/capabilities
 * - Épinglage des modèles favoris (localStorage)
 * - Filtrage par provider
 */
export function useModels() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data: providers = [] } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: () => apiClient.getProviders(),
  });

  const enabledProviders = providers.filter((p) => p.enabled);

  const { data: pinned = [] } = useQuery<PinnedModel[]>({
    queryKey: ["pinned-models"],
    queryFn: () => {
      if (typeof window === "undefined") return [];
      const raw = window.localStorage.getItem(STORAGE_PINNED);
      return raw ? JSON.parse(raw) : [];
    },
    staleTime: Infinity,
  });

  const setPinnedMutation = useMutation({
    mutationFn: (pinned: PinnedModel[]) => {
      if (typeof window === "undefined") return Promise.resolve();
      window.localStorage.setItem(STORAGE_PINNED, JSON.stringify(pinned));
      return Promise.resolve();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pinned-models"] });
    },
  });

  const pinModel = (providerId: string, modelId: string) => {
    const current = queryClient.getQueryData<PinnedModel[]>(["pinned-models"]) || [];
    const exists = current.some(
      (p) => p.providerId === providerId && p.modelId === modelId
    );
    if (exists) return;
    const next = [...current, { providerId, modelId, pinnedAt: new Date().toISOString() }];
    setPinnedMutation.mutate(next);
  };

  const unpinModel = (providerId: string, modelId: string) => {
    const current = queryClient.getQueryData<PinnedModel[]>(["pinned-models"]) || [];
    const next = current.filter(
      (p) => !(p.providerId === providerId && p.modelId === modelId)
    );
    setPinnedMutation.mutate(next);
  };

  const isPinned = (providerId: string, modelId: string) => {
    return pinned.some((p) => p.providerId === providerId && p.modelId === modelId);
  };

  const searchModels = (query: string): Array<ProviderModel & { providerId: string; providerName: string }> => {
    const q = query.toLowerCase().trim();
    const results: Array<ProviderModel & { providerId: string; providerName: string }> = [];

    for (const provider of enabledProviders) {
      const models = provider.models || [];
      for (const modelId of models) {
        if (!q || modelId.toLowerCase().includes(q)) {
          results.push({
            id: modelId,
            name: modelId,
            context_length: 0,
            is_local: provider.type === "ollama" || provider.type === "llamacpp",
            is_private: false,
            quality_score: 0,
            capabilities: [],
            providerId: provider.id,
            providerName: provider.name,
          });
        }
      }
    }

    return results;
  };

  return {
    providers,
    enabledProviders,
    pinned,
    pinModel,
    unpinModel,
    isPinned,
    searchModels,
  };
}