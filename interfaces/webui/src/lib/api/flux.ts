/**
 * ETHAN WebUI — Flux / Events API service
 *
 * Maps Open-WebUI log patterns to ETHAN API endpoints:
 *   OWUI: GET  /api/v1/logs           → ETHAN: GET  /v1/flux
 *   OWUI: GET  /api/v1/logs/{id}      → ETHAN: GET  /v1/flux/{id}
 *
 * Flux events are Core-owned (core/state/webui_store.py). The WebUI only
 * displays and sends actions.
 *
 * Types are the canonical ones from @/types.
 */

import { apiFetch } from '@/lib/api/client';
import type { FluxEvent } from '@/types';

/** List flux events */
export async function listFluxEvents(
	limit: number = 50,
	type?: string,
): Promise<FluxEvent[]> {
	const params = new URLSearchParams({ limit: String(limit) });
	if (type) params.set('type', type);
	return apiFetch<FluxEvent[]>(`/v1/flux?${params}`);
}

/** Get a single flux event */
export async function getFluxEvent(id: string): Promise<FluxEvent> {
	return apiFetch<FluxEvent>(`/v1/flux/${id}`);
}

export type { FluxEvent };
