/**
 * ETHAN WebUI — Memory API service
 *
 * Maps Open-WebUI memory patterns to ETHAN API endpoints:
 *   OWUI: GET  /api/v1/memory           → ETHAN: GET  /v1/memory/facts
 *   OWUI: POST /api/v1/memory           → ETHAN: POST /v1/memory/facts
 *   OWUI: GET  /api/v1/memory/search    → ETHAN: GET  /v1/memory/facts/search
 *
 * Memory (facts) is distinct from Knowledge (documents) and Conversation
 * (chat history). Facts are injected into the system prompt by ChatPipeline.
 *
 * Types are the canonical ones from @/types.
 */

import { apiFetch } from '@/lib/api/client';
import type { Fact, MemoryEvent } from '@/types';

/** List all memory facts */
export async function listFacts(
	limit: number = 20,
	category?: string,
): Promise<Fact[]> {
	const params = new URLSearchParams({ limit: String(limit) });
	if (category) params.set('category', category);
	return apiFetch<Fact[]>(`/v1/memory/facts?${params}`);
}

/** Search memory facts */
export async function searchFacts(query: string): Promise<Fact[]> {
	return apiFetch<Fact[]>(
		`/v1/memory/facts/search?q=${encodeURIComponent(query)}`,
	);
}

/** Get a single fact */
export async function getFact(id: string): Promise<Fact> {
	return apiFetch<Fact>(`/v1/memory/facts/${id}`);
}

/** Create a memory fact */
export async function createFact(data: {
	subject: string;
	predicate?: string;
	object: string;
	category?: string;
	confidence?: number;
}): Promise<Fact> {
	return apiFetch<Fact>('/v1/memory/facts', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Delete a memory fact */
export async function deleteFact(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/memory/facts/${id}`, {
		method: 'DELETE',
	});
}

/** List memory events */
export async function listMemoryEvents(): Promise<MemoryEvent[]> {
	return apiFetch<MemoryEvent[]>('/v1/memory/events');
}

/** Ingest a memory event */
export async function ingestMemory(entry: Record<string, unknown>): Promise<MemoryEvent> {
	return apiFetch<MemoryEvent>('/v1/memory/ingest', {
		method: 'POST',
		body: JSON.stringify(entry),
	});
}

/** Get a single memory entry (event or fact) */
export async function getMemoryEntry(id: string): Promise<MemoryEvent | Fact> {
	return apiFetch<MemoryEvent | Fact>(`/v1/memory/${id}`);
}

/** Search across all memory */
export async function searchMemory(
	query: string,
	filters?: Record<string, unknown>,
): Promise<Fact[]> {
	return apiFetch<Fact[]>('/v1/memory/search', {
		method: 'POST',
		body: JSON.stringify({ q: query, filters }),
	});
}

export type { Fact, MemoryEvent };
