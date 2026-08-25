/**
 * ETHAN WebUI — Goals API service
 *
 * Maps Open-WebUI goal patterns to ETHAN API endpoints:
 *   OWUI: /api/v1/goals         → ETHAN: /v1/goals
 *
 * Goals are Core-owned (core/goals). The WebUI only displays and sends actions.
 * Types are the canonical ones from @/types.
 */

import { apiFetch } from '@/lib/api/client';
import type { Goal } from '@/types';

export async function listGoals(): Promise<Goal[]> {
	return apiFetch<Goal[]>('/v1/goals');
}

export async function getGoal(id: string): Promise<Goal> {
	return apiFetch<Goal>(`/v1/goals/${id}`);
}

export async function createGoal(data: {
	title: string;
	description?: string;
	priority?: string;
}): Promise<Goal> {
	return apiFetch<Goal>('/v1/goals', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

export async function updateGoal(id: string, data: Record<string, unknown>): Promise<Goal> {
	return apiFetch<Goal>(`/v1/goals/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

export async function deleteGoal(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/goals/${id}`, {
		method: 'DELETE',
	});
}

export type { Goal };