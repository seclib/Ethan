"use client";

import { useCallback } from "react";
import { useMemoryStore } from "@/stores/memory.store";
import { memoryService } from "@/services/memory.service";
import type { Fact, MemoryEvent } from "@/types";

export function useFacts() {
  const { facts, isLoading, error, setFacts, setLoading, setError } = useMemoryStore();

  const fetchFacts = useCallback(async (filters?: Record<string, string>) => {
    setLoading(true);
    try {
      const query = filters?.query || "";
      const response = await memoryService.search(query, filters);
      setFacts(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch facts");
    } finally {
      setLoading(false);
    }
  }, [setFacts, setLoading, setError]);

  return { facts, isLoading, error, fetchFacts };
}

export function useMemoryEvents() {
  const { events, isLoading, error, setEvents, setLoading, setError } = useMemoryStore();

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const response = await memoryService.getAll();
      setEvents(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch events");
    } finally {
      setLoading(false);
    }
  }, [setEvents, setLoading, setError]);

  return { events, isLoading, error, fetchEvents };
}

export function useStoreMemory() {
  const { isLoading, setLoading, setError } = useMemoryStore();

  const mutate = useCallback(
    async (entry: any) => {
      setLoading(true);
      try {
        const response = await memoryService.store(entry);
        return { data: response.data, error: null };
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to store memory";
        setError(message);
        return { data: null, error: message };
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError]
  );

  return { mutate };
}