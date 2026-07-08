"use client";

import { useCallback, useEffect } from "react";
import { useAgentsStore } from "@/stores/agents.store";

export function useAgents() {
  const { agents, isLoading, error, fetchAgents, clearError } = useAgentsStore();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return {
    agents,
    isLoading,
    error,
    refetch: fetchAgents,
    clearError,
  };
}

export function useAgent(id: string | null) {
  const { agents, isLoading, error, fetchAgents, clearError } = useAgentsStore();

  useEffect(() => {
    if (id && !agents.find((a) => a.id === id)) {
      fetchAgents();
    }
  }, [id, agents, fetchAgents]);

  const agent = id ? agents.find((a) => a.id === id) || null : null;

  return {
    agent,
    isLoading,
    error,
    clearError,
  };
}

export function useCreateAgent() {
  const { createAgent, isLoading, error, clearError } = useAgentsStore();

  const mutate = useCallback(
    async (data: { name: string; capabilities?: string[] }) => {
      try {
        const agent = await createAgent(data);
        return { data: agent, error: null };
      } catch (error) {
        return { data: null, error: error instanceof Error ? error.message : "Failed to create agent" };
      }
    },
    [createAgent]
  );

  return {
    mutate,
    isLoading,
    error,
    clearError,
  };
}

export function useUpdateAgent() {
  const { updateAgent, isLoading, error, clearError } = useAgentsStore();

  const mutate = useCallback(
    async (id: string, data: { name?: string; capabilities?: string[] }) => {
      try {
        const agent = await updateAgent(id, data);
        return { data: agent, error: null };
      } catch (error) {
        return { data: null, error: error instanceof Error ? error.message : "Failed to update agent" };
      }
    },
    [updateAgent]
  );

  return {
    mutate,
    isLoading,
    error,
    clearError,
  };
}

export function useDeleteAgent() {
  const { deleteAgent, isLoading, error, clearError } = useAgentsStore();

  const mutate = useCallback(
    async (id: string) => {
      try {
        await deleteAgent(id);
        return { error: null };
      } catch (error) {
        return { error: error instanceof Error ? error.message : "Failed to delete agent" };
      }
    },
    [deleteAgent]
  );

  return {
    mutate,
    isLoading,
    error,
    clearError,
  };
}