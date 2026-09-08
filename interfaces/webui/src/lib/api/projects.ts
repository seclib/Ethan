/**
 * ETHAN WebUI — Projects API service
 *
 * Maps to ETHAN Core's ProjectManager (interfaces.api.routers.projects):
 *   GET  /v1/projects              → list (scope utilisateur)
 *   POST /v1/projects              → create
 *   GET  /v1/projects/default      → fallback « General (Default) »
 *   GET  /v1/projects/{id}         → get
 *   PATCH /v1/projects/{id}        → update
 *   DELETE /v1/projects/{id}       → delete (logique, chats préservés)
 *   GET  /v1/projects/{id}/context → contexte d'exécution (ChatPipeline)
 *
 * Documents du projet (délégation au pipeline Core) :
 *   GET  /v1/projects/{id}/documents → liste
 *   POST /v1/projects/{id}/documents → upload multipart
 *   DELETE /v1/projects/{id}/documents/{docId} → suppression
 *
 * A Project is a conversation container with knowledge scope + execution context.
 * WebUI is a passive client — all logic lives in core/projects.
 */

import { apiFetch } from '@/lib/api/client';

export interface Project {
	id: string;
	name: string;
	description?: string;
	instructions?: string;
	user_id: string;
	folder_ids: string[];
	knowledge_ids: string[];
	collection_ids: string[];
	skill_ids: string[];
	tool_ids: string[];
	agent_id?: string;
	provider_id?: string;
	model?: string;
	metadata: Record<string, unknown>;
	is_active?: boolean;
	created_at: string;
	updated_at: string;
}

export interface ProjectSelection {
	active_project_id: string | null;
}

/** Résolu par le Core — contexte d'exécution utilisé par ChatPipeline. */
export interface ProjectContext {
	id: string;
	name: string;
	instructions?: string;
	agent_id?: string;
	provider_id?: string;
	model?: string;
	folder_ids: string[];
	knowledge_ids: string[];
	collection_ids: string[];
	skill_ids: string[];
	tool_ids: string[];
}

/** Document RAG rattaché à un projet (lecture seule côté WebUI). */
export interface ProjectDocument {
	id: string;
	filename: string;
	mime_type: string;
	size_bytes: number;
	status: 'processing' | 'ready' | 'failed';
	chunk_count?: number;
	error?: string;
	created_at: string;
}

/** Liste des documents d'un projet (Core-owned, scope projet). */
export async function listProjectDocuments(projectId: string): Promise<ProjectDocument[]> {
	return apiFetch<ProjectDocument[]>(`/v1/projects/${projectId}/documents`);
}

/** Upload un fichier dans un projet (multipart → pipeline Core). */
export async function uploadProjectDocument(
	projectId: string,
	file: File,
	onProgress?: (pct: number) => void,
): Promise<ProjectDocument> {
	const fd = new FormData();
	fd.append('file', file);
	// Progress via XMLHttpRequest si demandé, sinon fetch simple.
	if (onProgress) {
		return _uploadWithProgress<ProjectDocument>(`/v1/projects/${projectId}/documents`, fd, onProgress);
	}
	return apiFetch<ProjectDocument>(`/v1/projects/${projectId}/documents`, {
		method: 'POST',
		body: fd,
	});
}

/** Suppression d'un document (scope projet, 403 si hors scope). */
export async function deleteProjectDocument(
	projectId: string,
	docId: string,
): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/projects/${projectId}/documents/${docId}`, {
		method: 'DELETE',
	});
}

/** List all projects for current user */
export async function listProjects(): Promise<Project[]> {
	return apiFetch<Project[]>('/v1/projects');
}

/** Get default project (fallback « General »). */
export async function getDefaultProject(): Promise<Project> {
	return apiFetch<Project>('/v1/projects/default');
}

/** Get a single project by ID */
export async function getProject(id: string): Promise<Project> {
	return apiFetch<Project>(`/v1/projects/${id}`);
}

/** Create a new project */
export async function createProject(data: Partial<Project>): Promise<Project> {
	return apiFetch<Project>('/v1/projects', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Update an existing project */
export async function updateProject(id: string, data: Partial<Project>): Promise<Project> {
	return apiFetch<Project>(`/v1/projects/${id}`, {
		method: 'PATCH',
		body: JSON.stringify(data),
	});
}

/** Delete a project */
export async function deleteProject(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/projects/${id}`, {
		method: 'DELETE',
	});
}

/** Select active project (sets cookie/header for subsequent requests) */
export async function selectProject(id: string | null): Promise<ProjectSelection> {
	return apiFetch<ProjectSelection>('/v1/projects/active', {
		method: 'POST',
		body: JSON.stringify({ active_project_id: id }),
	});
}

/** Contexte d'exécution d'un projet (agents, modèle, ressources). */
export async function getProjectContext(projectId: string): Promise<ProjectContext> {
	return apiFetch<ProjectContext>(`/v1/projects/${projectId}/context`);
}

/** Upload avec progression (XHR). */
function _uploadWithProgress<T>(url: string, fd: FormData, onProgress: (pct: number) => void): Promise<T> {
	return new Promise((resolve, reject) => {
		const xhr = new XMLHttpRequest();
		xhr.open('POST', url);
		xhr.upload.onprogress = (e) => {
			if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
		};
		xhr.onload = () => {
			if (xhr.status >= 200 && xhr.status < 300) {
				try { resolve(JSON.parse(xhr.responseText) as T); } catch { reject(new Error('Invalid JSON')); }
			} else {
				reject(new Error(`Upload failed: ${xhr.status}`));
			}
		};
		xhr.onerror = () => reject(new Error('Network error'));
		const token = typeof window !== 'undefined' ? localStorage.getItem('ethan_token') : null;
		if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
		xhr.send(fd);
	});
}
