/**
 * ETHAN WebUI — Folders API service
 *
 * Client passif des dossiers génériques Core (/v1/folders).  Toute la
 * logique (arborescence, relations multi-ressources, validation) appartient
 * au Core (core/folders) : cette couche n'affiche et ne transmet que des
 * intentions utilisateur.
 */

import { apiFetch } from '@/lib/api/client';

export type FolderResourceType = "knowledge" | "collection" | "skill";

export interface Folder {
	id: string;
	name: string;
	description: string;
	user_id: string;
	/** Dossier parent (arborescence libre créée par l'utilisateur). */
	parent_id: string | null;
	icon: string | null;
	order: number;
	metadata: Record<string, unknown>;
	created_at: string;
	updated_at: string;
}

export interface FolderTree extends Folder {
	/** Nombre de ressources directement classées dans le dossier. */
	resource_count: number;
	children: FolderTree[];
}

export interface FolderResource {
	resource_type: FolderResourceType;
	resource_id: string;
	/** Record réel résolu par le manager Core propriétaire. */
	record: Record<string, unknown> | null;
}

export async function listFolderTree(userId?: string): Promise<FolderTree[]> {
	const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
	return apiFetch<FolderTree[]>(`/v1/folders/tree${query}`);
}

export async function getFolder(folderId: string): Promise<Folder> {
	return apiFetch<Folder>(`/v1/folders/${folderId}`);
}

export async function createFolder(data: {
	name: string;
	description?: string;
	user_id?: string;
	parent_id?: string | null;
	icon?: string | null;
	order?: number;
}): Promise<Folder> {
	return apiFetch<Folder>("/v1/folders", {
		method: "POST",
		body: JSON.stringify(data),
	});
}

export async function updateFolder(
	folderId: string,
	data: {
		name?: string;
		description?: string;
		icon?: string | null;
		order?: number;
		parent_id?: string | null;
	},
): Promise<Folder> {
	return apiFetch<Folder>(`/v1/folders/${folderId}`, {
		method: "PATCH",
		body: JSON.stringify(data),
	});
}

export async function moveFolder(
	folderId: string,
	parentId: string | null,
): Promise<Folder> {
	return apiFetch<Folder>(`/v1/folders/${folderId}/move`, {
		method: "POST",
		body: JSON.stringify({ parent_id: parentId }),
	});
}

export async function deleteFolder(folderId: string): Promise<void> {
	await apiFetch(`/v1/folders/${folderId}`, { method: "DELETE" });
}

export async function listFolderResources(
	folderId: string,
	resourceType?: FolderResourceType,
): Promise<FolderResource[]> {
	const query = resourceType ? `?resource_type=${resourceType}` : "";
	return apiFetch<FolderResource[]>(`/v1/folders/${folderId}/resources${query}`);
}

export async function attachFolderResource(
	folderId: string,
	resourceType: FolderResourceType,
	resourceId: string,
): Promise<void> {
	await apiFetch(`/v1/folders/${folderId}/resources`, {
		method: "POST",
		body: JSON.stringify({ resource_type: resourceType, resource_id: resourceId }),
	});
}

export async function detachFolderResource(
	folderId: string,
	resourceType: FolderResourceType,
	resourceId: string,
): Promise<void> {
	await apiFetch(
		`/v1/folders/${folderId}/resources/${resourceType}/${resourceId}`,
		{ method: "DELETE" },
	);
}

/** Déplace une ressource vers l'ensemble de dossiers donné (remplacement ; [] = sans dossier). */
export async function moveResource(
	resourceType: FolderResourceType,
	resourceId: string,
	folderIds: string[],
): Promise<{ folder_ids: string[] }> {
	return apiFetch<{ folder_ids: string[] }>("/v1/folders/move-resource", {
		method: "POST",
		body: JSON.stringify({
			resource_type: resourceType,
			resource_id: resourceId,
			folder_ids: folderIds,
		}),
	});
}

/** Ressources d'un type classées dans aucun dossier. */
export async function listUntaggedResources(
	resourceType: FolderResourceType,
): Promise<Record<string, unknown>[]> {
	return apiFetch<Record<string, unknown>[]>(
		`/v1/folders/untagged?resource_type=${resourceType}`,
	);
}

/** Dossiers contenant une ressource (multi-membership possible). */
export async function listFoldersOfResource(
	resourceType: FolderResourceType,
	resourceId: string,
): Promise<Folder[]> {
	return apiFetch<Folder[]>(
		`/v1/folders/by-resource/${resourceType}/${resourceId}`,
	);
}

/** Index batch `{resource_id: [folder_id, ...]}` — filtrage des listes par dossier. */
export async function getFolderIndex(
	resourceType?: FolderResourceType,
): Promise<Record<string, string[]>> {
	const query = resourceType ? `?resource_type=${resourceType}` : "";
	return apiFetch<Record<string, string[]>>(`/v1/folders/index${query}`);
}
