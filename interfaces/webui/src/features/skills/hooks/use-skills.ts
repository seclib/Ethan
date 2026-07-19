"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { skillsService } from "@/features/skills/services/skills.service";
import type { Skill } from "@/types";

export function useSkills() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["skills"],
    queryFn: () => skillsService.getAll(),
  });

  return { 
    skills: data?.data || [], 
    isLoading, 
    error: error instanceof Error ? error.message : null, 
    refetch 
  };
}

export function useSkill(id: string | null) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["skills", id],
    queryFn: () => id ? skillsService.getById(id) : null,
    enabled: !!id,
  });

  return { 
    skill: data?.data || null, 
    isLoading, 
    error: error instanceof Error ? error.message : null, 
    refetch 
  };
}

export function useTestSkill() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (id: string) => skillsService.test(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      queryClient.invalidateQueries({ queryKey: ["skills", id] });
    },
  });

  return {
    mutate: async (id: string) => {
      try {
        const result = await mutation.mutateAsync(id);
        return { passed: result.data.passed, output: result.data.output, error: null };
      } catch (err) {
        return { passed: false, output: "", error: err instanceof Error ? err.message : "Failed to test skill" };
      }
    },
    isLoading: mutation.isPending
  };
}

export function useInstallSkill() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (id: string) => skillsService.install(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      queryClient.invalidateQueries({ queryKey: ["skills", id] });
    },
  });

  return {
    mutate: async (id: string) => {
      try {
        const result = await mutation.mutateAsync(id);
        return { data: result.data, error: null };
      } catch (err) {
        return { data: null, error: err instanceof Error ? err.message : "Failed to install skill" };
      }
    },
    isLoading: mutation.isPending
  };
}