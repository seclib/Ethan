"use client";

import { useCallback } from "react";
import { useSkillsStore } from "@/stores/skills.store";
import { skillsService } from "@/services/skills.service";

export function useSkills() {
  const { skills, isLoading, error, setSkills, setLoading, setError } = useSkillsStore();

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    try {
      const response = await skillsService.getAll();
      setSkills(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch skills");
    } finally {
      setLoading(false);
    }
  }, [setSkills, setLoading, setError]);

  return { skills, isLoading, error, refetch: fetchSkills };
}

export function useSkill(id: string | null) {
  const { skills, isLoading, error, setLoading, setError } = useSkillsStore();

  const skill = id ? skills.find((s) => s.id === id) || null : null;

  const fetchSkill = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await skillsService.getById(id);
      useSkillsStore.getState().updateSkill(id, response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch skill");
    } finally {
      setLoading(false);
    }
  }, [id, setLoading, setError]);

  return { skill, isLoading, error, refetch: fetchSkill };
}

export function useTestSkill() {
  const { updateSkill, setLoading, setError } = useSkillsStore();

  const mutate = useCallback(
    async (id: string) => {
      setLoading(true);
      try {
        const response = await skillsService.test(id);
        updateSkill(id, {
          ...(response.data.passed ? { status: "active" as const } : { status: "candidate" as const }),
        } as any);
        return { passed: response.data.passed, output: response.data.output, error: null };
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to test skill";
        setError(message);
        return { passed: false, output: "", error: message };
      } finally {
        setLoading(false);
      }
    },
    [updateSkill, setLoading, setError]
  );

  return { mutate };
}

export function useInstallSkill() {
  const { updateSkill, setLoading, setError } = useSkillsStore();

  const mutate = useCallback(
    async (id: string) => {
      setLoading(true);
      try {
        const response = await skillsService.install(id);
        updateSkill(id, response.data);
        return { data: response.data, error: null };
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to install skill";
        setError(message);
        return { data: null, error: message };
      } finally {
        setLoading(false);
      }
    },
    [updateSkill, setLoading, setError]
  );

  return { mutate };
}