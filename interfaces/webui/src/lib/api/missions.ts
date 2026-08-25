/**
 * ETHAN WebUI — Missions API service
 *
 * Maps Open-WebUI mission patterns to ETHAN API endpoints:
 *   OWUI: /api/v1/missions         → ETHAN: /v1/missions
 *
 * Missions are Core-owned (core/missions). The WebUI only displays and sends actions.
 * Types are the canonical ones from @/types.
 */

import { apiFetch } from '@/lib/api/client';
import type { Mission } from '@/types';

export async function listMissions(status?: string): Promise<Mission[]> {
	const qs = status ? `?status=${encodeURIComponent(status)}` : '';
	return apiFetch<Mission[]>(`/v1/missions${qs}`);
}

export async function getMission(id: string): Promise<Mission> {
	return apiFetch<Mission>(`/v1/missions/${id}`);
}

export async function createMission(data: {
	title: string;
	description?: string;
	steps?: unknown[];
	workspace_path?: string;
	metadata?: Record<string, unknown>;
}): Promise<Mission> {
	return apiFetch<Mission>('/v1/missions', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

export async function updateMission(id: string, data: Record<string, unknown>): Promise<Mission> {
	return apiFetch<Mission>(`/v1/missions/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

export async function deleteMission(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/missions/${id}`, {
		method: 'DELETE',
	});
}

export async function verifyMissionStep(missionId: string, stepId: string): Promise<unknown> {
	return apiFetch(`/v1/missions/${missionId}/steps/${stepId}/verify`, {
		method: 'POST',
	});
}

export async function approveMissionStep(missionId: string, stepId: string): Promise<unknown> {
	return apiFetch(`/v1/missions/${missionId}/steps/${stepId}/approve`, {
		method: 'POST',
	});
}

export type { Mission };