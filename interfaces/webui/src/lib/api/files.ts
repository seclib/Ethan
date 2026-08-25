/**
 * ETHAN WebUI — Files API service
 *
 * Maps Open-WebUI file patterns to ETHAN API endpoints:
 *   OWUI: GET  /api/v1/files           → ETHAN: GET  /files
 *   OWUI: POST /api/v1/files/upload    → ETHAN: POST /files/upload
 *   OWUI: GET  /api/v1/files/{id}      → ETHAN: GET  /files/{id}
 *   OWUI: DEL  /api/v1/files/{id}      → ETHAN: DELETE /files/{id}
 *
 * Files are Core-owned (core/state/files.py). The WebUI only displays and
 * sends upload/download actions.
 */

import { apiFetch } from '@/lib/api/client';

export interface FileRecord {
	id: string;
	filename: string;
	content_type: string;
	size: number;
	user_id: string;
	storage_path?: string | null;
	metadata: Record<string, unknown>;
	has_content?: boolean;
	created_at: string;
}

/** List all files */
export async function listFiles(userId?: string): Promise<FileRecord[]> {
	const qs = userId ? `?user_id=${encodeURIComponent(userId)}` : '';
	return apiFetch<FileRecord[]>(`/files${qs}`);
}

/** Get a single file metadata */
export async function getFile(id: string): Promise<FileRecord> {
	return apiFetch<FileRecord>(`/files/${id}`);
}

/** Upload a binary file to ETHAN Core */
export async function uploadFile(
	file: File,
	userId: string = 'anonymous',
): Promise<FileRecord> {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('user_id', userId);

	const response = await fetch('/api/files/upload', {
		method: 'POST',
		credentials: 'include',
		body: formData,
	});

	if (!response.ok) {
		let body: unknown;
		try {
			body = await response.json();
		} catch {
			body = await response.text();
		}
		const message =
			(body as { detail?: string })?.detail || `HTTP ${response.status}`;
		throw new Error(message);
	}

	return response.json() as Promise<FileRecord>;
}

/** Download a file from ETHAN Core */
export async function downloadFile(id: string): Promise<Blob> {
	const response = await fetch(`/api/files/${id}/download`, {
		method: 'GET',
		credentials: 'include',
	});

	if (!response.ok) {
		throw new Error(`HTTP ${response.status}`);
	}

	return response.blob();
}

/** Delete a file */
export async function deleteFile(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/files/${id}`, {
		method: 'DELETE',
	});
}