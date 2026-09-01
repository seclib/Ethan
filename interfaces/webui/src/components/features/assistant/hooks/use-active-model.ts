"use client";

import { useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listProviders, setDefaultProvider, type Provider } from "@/lib/api/providers";
import { listProviderModels } from "@/lib/api/providers";
import { useUIStore } from "@/store/ui.store";
import { useModelStore } from "@/store/model.store";

/**
 * Hook centralisé de sélection du moteur IA actif.
 * - L'état (provider + modèle) vit dans `useModelStore` (zustand) : source
 *   unique partagée par ModelSelector, ProviderSelector, la top bar et la
 *   page chat — la sélection est donc réellement propagée au payload chat.
 * - Charge les providers via /providers (ProviderManager Core)
 * - Synchronise le provider par défaut côté backend (PUT /providers/{id}/default)
 */
export function useActiveModel() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const selectedProviderId = useModelStore((s) => s.selectedProviderId);
  const selectedModel = useModelStore((s) => s.selectedModel);
  const setSelection = useModelStore((s) => s.setSelection);
  const setModelStore = useModelStore((s) => s.setModel);

  const { data: providers = [] } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: () => listProviders(),
  });

  const defaultProvider = providers.find((p) => p.is_default) || providers.find((p) => p.enabled);

  // Résolution du provider par défaut une fois les providers chargés
  // (uniquement si aucune sélection utilisateur valide).
  useEffect(() => {
    if (defaultProvider && !selectedProviderId) {
      setSelection(defaultProvider.id, defaultProvider.default_model || "");
    }
  }, [defaultProvider, selectedProviderId, setSelection]);

  const activeProvider = providers.find((p) => p.id === selectedProviderId) || defaultProvider;

  const { data: models = [] } = useQuery<unknown[]>({
    queryKey: ["provider-models", selectedProviderId],
    queryFn: () => listProviderModels(selectedProviderId),
    enabled: !!selectedProviderId,
  });

  const setDefaultMutation = useMutation({
    mutationFn: (id: string) => setDefaultProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Active engine updated" });
    },
    onError: (err) => {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to switch engine",
      });
    },
  });

  const setProvider = useCallback(
    (id: string) => {
      const p = providers.find((x) => x.id === id);
      setSelection(id, p?.default_model || "");
      if (p && !p.is_default) setDefaultMutation.mutate(id);
    },
    [providers, setSelection, setDefaultMutation],
  );

  const setModel = useCallback(
    (model: string) => {
      setModelStore(model);
    },
    [setModelStore],
  );

  return {
    providers,
    models,
    activeProvider,
    enabledProviders: providers.filter((p) => p.enabled),
    selectedProviderId,
    selectedModel,
    setProvider,
    setModel,
    isPending: setDefaultMutation.isPending,
  };
}
