import { useCallback, useEffect } from "react";
import { useGoalsStore } from "@/stores/goals.store";

export function useGoals() {
  const { goals, isLoading, error, fetchGoals, clearError } = useGoalsStore();

  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]);

  return {
    goals,
    isLoading,
    error,
    refetch: fetchGoals,
    clearError,
  };
}

export function useGoal(id: string | null) {
  const { goals, isLoading, error, fetchGoals, selectGoal, clearError } = useGoalsStore();

  useEffect(() => {
    if (id && !goals.find((g) => g.id === id)) {
      fetchGoals();
    }
  }, [id, goals, fetchGoals]);

  useEffect(() => {
    if (id) {
      selectGoal(id);
    }
  }, [id, selectGoal]);

  const goal = id ? goals.find((g) => g.id === id) || null : null;

  return {
    goal,
    isLoading,
    error,
    clearError,
  };
}

export function useCreateGoal() {
  const { createGoal, isLoading, error, clearError } = useGoalsStore();

  const mutate = useCallback(
    async (data: { title: string; description?: string; priority?: string }) => {
      try {
        const goal = await createGoal(data);
        return { data: goal, error: null };
      } catch (error) {
        return { data: null, error: error instanceof Error ? error.message : "Failed to create goal" };
      }
    },
    [createGoal]
  );

  return {
    mutate,
    isLoading,
    error,
    clearError,
  };
}

export function useUpdateGoal() {
  const { updateGoal, isLoading, error, clearError } = useGoalsStore();

  const mutate = useCallback(
    async (id: string, data: { title?: string; description?: string; priority?: "high" | "medium" | "low" }) => {
      try {
        const goal = await updateGoal(id, data);
        return { data: goal, error: null };
      } catch (error) {
        return { data: null, error: error instanceof Error ? error.message : "Failed to update goal" };
      }
    },
    [updateGoal]
  );

  return {
    mutate,
    isLoading,
    error,
    clearError,
  };
}

export function useDeleteGoal() {
  const { deleteGoal, isLoading, error, clearError } = useGoalsStore();

  const mutate = useCallback(
    async (id: string) => {
      try {
        await deleteGoal(id);
        return { error: null };
      } catch (error) {
        return { error: error instanceof Error ? error.message : "Failed to delete goal" };
      }
    },
    [deleteGoal]
  );

  return {
    mutate,
    isLoading,
    error,
    clearError,
  };
}