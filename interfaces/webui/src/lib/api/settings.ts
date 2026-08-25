/**
 * ETHAN WebUI — Settings API service
 *
 * Maps Open-WebUI settings patterns to ETHAN API endpoints:
 *   OWUI: GET  /api/v1/settings       → ETHAN: GET  /v1/settings
 *   OWUI: PUT  /api/v1/settings       → ETHAN: PUT  /v1/settings
 *
 * Settings are Core-owned (core/state/webui_store.py). The WebUI only
 * displays and sends actions.
 *
 * Types are the canonical ones from @/types.
 */

import { apiFetch } from '@/lib/api/client';
import type { Settings } from '@/types';

/** Get system settings */
export async function getSettings(): Promise<Settings> {
	return apiFetch<Settings>('/v1/settings');
}

/** Update system settings */
export async function updateSettings(data: Partial<Settings>): Promise<Settings> {
	return apiFetch<Settings>('/v1/settings', {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

export type { Settings };
