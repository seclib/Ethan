/**
 * ETHAN WebUI — Skills API service
 *
 * Maps Open-WebUI skills patterns to ETHAN API endpoints:
 *   OWUI: GET  /api/v1/skills          → ETHAN: GET  /v1/skills
 *   OWUI: POST /api/v1/skills           → ETHAN: POST /v1/skills
 *   OWUI: GET  /api/v1/skills/{id}     → ETHAN: GET  /v1/skills/{id}
 *   OWUI: POST /api/v1/skills/{id}/toggle → ETHAN: POST /v1/skills/{id}/toggle
 *
 * Skills are Core-owned (core/skills/store.py). The WebUI only displays and
 * sends actions.
 */

import { apiFetch } from '@/lib/api/client';

export interface Skill {
	id: string;
	name: string;
	description: string;
	content: string;
	version: string;
	status: string;
	is_active: boolean;
	tags: string[];
	meta: Record<string, unknown>;
	created_at: string;
	updated_at: string;
}

/** List all skills */
export async function listSkills(): Promise<Skill[]> {
	return apiFetch<Skill[]>('/v1/skills');
}

/** Search skills */
export async function searchSkills(query: string): Promise<Skill[]> {
	return apiFetch<Skill[]>(`/v1/skills/search?q=${encodeURIComponent(query)}`);
}

/** Get a single skill */
export async function getSkill(id: string): Promise<Skill> {
	return apiFetch<Skill>(`/v1/skills/${id}`);
}

/** Create a skill */
export async function createSkill(data: {
	name: string;
	description?: string;
	content?: string;
	version?: string;
	tags?: string[];
	meta?: Record<string, unknown>;
}): Promise<Skill> {
	return apiFetch<Skill>('/v1/skills', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Update a skill */
export async function updateSkill(id: string, data: Record<string, unknown>): Promise<Skill> {
	return apiFetch<Skill>(`/v1/skills/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

/** Delete a skill */
export async function deleteSkill(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/skills/${id}`, {
		method: 'DELETE',
	});
}

/** Toggle skill active state */
export async function toggleSkill(id: string): Promise<Skill> {
	return apiFetch<Skill>(`/v1/skills/${id}/toggle`, {
		method: 'POST',
	});
}

/** Execute a skill */
export async function executeSkill(
	id: string,
	params: Record<string, unknown>,
): Promise<{ skill_id: string; status: string; result: unknown }> {
	return apiFetch<{ skill_id: string; status: string; result: unknown }>(
		`/v1/skills/${id}/execute`,
		{
			method: 'POST',
			body: JSON.stringify(params),
		},
	);
}
