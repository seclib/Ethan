"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { missionsService } from "@/features/missions/services/missions.service";
import type { Mission } from "@/types";

export function useMissions() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["missions"],
    queryFn: () => missionsService.getAll(),
  });

  return { 
    missions: data?.data || [], 
    isLoading, 
    error: error instanceof Error ? error.message : null, 
    refetch 
  };
}

export function useMission(id: string | null) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["missions", id],
    queryFn: () => id ? missionsService.getById(id) : null,
    enabled: !!id,
  });

  return { 
    mission: data?.data || null, 
    isLoading, 
    error: error instanceof Error ? error.message : null 
  };
}

export function useCreateMission() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (data: { title: string; description: string }) => missionsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["missions"] });
    },
  });

  return {
    mutate: async (data: { title: string; description: string }) => {
      try {
        const result = await mutation.mutateAsync(data);
        return { data: result.data, error: null };
      } catch (err) {
        return { data: null, error: err instanceof Error ? err.message : "Failed to create mission" };
      }
    },
    isLoading: mutation.isPending
  };
}

export function useVerifyStep() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ missionId, stepId }: { missionId: string; stepId: string }) => 
      missionsService.verifyStep(missionId, stepId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["missions"] });
      queryClient.invalidateQueries({ queryKey: ["missions", variables.missionId] });
    },
  });

  return {
    mutate: async (missionId: string, stepId: string) => {
      try {
        const result = await mutation.mutateAsync({ missionId, stepId });
        return { verified: result.data.verified, error: null };
      } catch (err) {
        return { verified: false, error: err instanceof Error ? err.message : "Failed to verify step" };
      }
    },
    isLoading: mutation.isPending
  };
}