"use client";

import { useCallback, useEffect } from "react";
import { useMissionsStore } from "@/stores/missions.store";
import { missionsService } from "@/services/missions.service";

export function useMissions() {
  const { missions, isLoading, error, setMissions, setLoading, setError } = useMissionsStore();

  const fetchMissions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await missionsService.getAll();
      setMissions(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch missions");
    } finally {
      setLoading(false);
    }
  }, [setMissions, setLoading, setError]);

  useEffect(() => {
    fetchMissions();
  }, [fetchMissions]);

  return { missions, isLoading, error, refetch: fetchMissions };
}

export function useMission(id: string | null) {
  const { missions, selectedMission, isLoading, error, selectMission, setLoading, setError } = useMissionsStore();

  useEffect(() => {
    if (!id) {
      selectMission(null);
      return;
    }
    const fetchMission = async () => {
      setLoading(true);
      try {
        const response = await missionsService.getById(id);
        selectMission(id);
        useMissionsStore.getState().updateMission(id, response.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch mission");
      } finally {
        setLoading(false);
      }
    };
    fetchMission();
  }, [id, selectMission, setLoading, setError]);

  const mission = id ? missions.find((m) => m.id === id) || null : null;

  return { mission, isLoading, error };
}

export function useCreateMission() {
  const { addMission, setLoading, setError } = useMissionsStore();

  const mutate = useCallback(
    async (data: { title: string; description: string }) => {
      setLoading(true);
      try {
        const response = await missionsService.create(data);
        addMission(response.data);
        return { data: response.data, error: null };
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to create mission";
        setError(message);
        return { data: null, error: message };
      } finally {
        setLoading(false);
      }
    },
    [addMission, setLoading, setError]
  );

  return { mutate };
}

export function useVerifyStep() {
  const { updateStep, setLoading, setError } = useMissionsStore();

  const mutate = useCallback(
    async (missionId: string, stepId: string) => {
      setLoading(true);
      try {
        const response = await missionsService.verifyStep(missionId, stepId);
        updateStep(missionId, stepId, { verified: response.data.verified });
        return { verified: response.data.verified, error: null };
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to verify step";
        setError(message);
        return { verified: false, error: message };
      } finally {
        setLoading(false);
      }
    },
    [updateStep, setLoading, setError]
  );

  return { mutate };
}