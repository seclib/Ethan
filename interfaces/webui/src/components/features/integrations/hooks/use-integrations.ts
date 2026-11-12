"use client";

/**
 * use-integrations — gestion des App Integrations ETHAN.
 *
 * Le WebUI ne gère QUE la configuration : lister, créer, configurer,
 * tester, connecter/déconnecter, supprimer. Toute la logique (identité,
 * credentials, capacités, permissions, health, lifecycle) vit dans le
 * IntegrationManager Core — les credentials ne sont JAMAIS renvoyés par
 * l'API (seuls leurs noms de clés le sont : `credential_keys`).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listIntegrations,
  getIntegration,
  createIntegration,
  updateIntegration,
  deleteIntegration,
  connectIntegration,
  disconnectIntegration,
  testIntegration,
  type Integration,
  type IntegrationCreate,
  type IntegrationUpdate,
  type IntegrationKind,
} from "@/lib/api/integrations";
import { useUIStore } from "@/store/ui.store";

const QUERY_KEY = "integrations";

export function useIntegrations(kind?: IntegrationKind) {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data: integrations = [], isLoading, error, refetch } = useQuery<Integration[]>({
    queryKey: [QUERY_KEY, kind ?? null],
    queryFn: () => listIntegrations(kind),
    staleTime: 15_000,
    retry: 1,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });

  // ── Mutations ────────────────────────────────────────────────────────
  const createMutation = useMutation({
    mutationFn: createIntegration,
    onSuccess: (data) => {
      invalidate();
      addToast({ type: "success", message: `Integration "${data.name}" created` });
    },
    onError: (err: Error) => {
      addToast({ type: "error", message: `Failed to create integration: ${err.message}` });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: IntegrationUpdate }) =>
      updateIntegration(id, data),
    onSuccess: (data) => {
      invalidate();
      addToast({ type: "success", message: `Integration "${data.name}" updated` });
    },
    onError: (err: Error) => {
      addToast({ type: "error", message: `Failed to update integration: ${err.message}` });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteIntegration,
    onSuccess: () => {
      invalidate();
      addToast({ type: "success", message: "Integration deleted (credentials purged)" });
    },
    onError: (err: Error) => {
      addToast({ type: "error", message: `Failed to delete: ${err.message}` });
    },
  });

  const connectMutation = useMutation({
    mutationFn: connectIntegration,
    onSuccess: (data) => {
      invalidate();
      if (data.status === "connected") {
        addToast({ type: "success", message: `Integration "${data.name}" connected` });
      } else {
        addToast({
          type: "error",
          message: `Connection failed: ${String(data.status ?? "healthcheck error")}`,
        });
      }
    },
    onError: (err: Error) => {
      addToast({ type: "error", message: `Connect failed: ${err.message}` });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: disconnectIntegration,
    onSuccess: (data) => {
      invalidate();
      addToast({ type: "success", message: `Integration "${data.name}" disconnected` });
    },
    onError: (err: Error) => {
      addToast({ type: "error", message: `Disconnect failed: ${err.message}` });
    },
  });

  const testMutation = useMutation({
    mutationFn: testIntegration,
    onSuccess: (data) => {
      invalidate();
      if (data.status === "connected") {
        addToast({ type: "success", message: `Connection test passed: ${data.message}` });
      } else {
        addToast({ type: "warning", message: `Test failed: ${data.message}` });
      }
    },
    onError: (err: Error) => {
      addToast({ type: "error", message: `Test failed: ${err.message}` });
    },
  });

  return {
    integrations,
    isLoading,
    error: error instanceof Error ? error.message : null,
    refetch,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isConnecting: connectMutation.isPending,
    isDisconnecting: disconnectMutation.isPending,
    isTesting: testMutation.isPending,

    createIntegrationAsync: (data: IntegrationCreate) => createMutation.mutateAsync(data),
    updateIntegrationAsync: (id: string, data: IntegrationUpdate) =>
      updateMutation.mutateAsync({ id, data }),
    deleteIntegrationAsync: (id: string) => deleteMutation.mutateAsync(id),
    connectAsync: (id: string) => connectMutation.mutateAsync(id),
    disconnectAsync: (id: string) => disconnectMutation.mutateAsync(id),
    testAsync: (id: string) => testMutation.mutateAsync(id),
  };
}