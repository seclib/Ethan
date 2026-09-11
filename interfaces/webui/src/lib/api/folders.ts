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
	/**
	 * Collection Knowledge associée (contexte de navigation) — référence
	 * validée par le Core ; un dossier n'est PAS un répertoire de la collection.
	 */
	collection_id: string | null;
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

export async function listFolderTree(
	userId?: string,
	collectionId?: string | null,
): Promise<FolderTree[]> {
	const params = new URLSearchParams();
	if (userId) params.set("user_id", userId);
	if (collectionId) params.set("collection_id", collectionId);
	const query = params.toString() ? `?${params.toString()}` : "";
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
	collection_id?: string | null;
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
		collection_id?: string | null;
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
// ── Consolidation (opérations explicites, rapport Core) ─────────────────────

/** Rapport d'opération retourné par le Core — les partiels sont visibles. */
export interface FolderOperationReport {
	operation_id: string;
	operation: "merge" | "copy" | "move";
	status: "completed" | "partially_completed" | "failed";
	attached: number;
	moved: number;
	skipped: number;
	errors: string[];
	target_id?: string;
	sources?: string[];
	removed_sources?: string[];
}

export interface FolderResourceRef {
	resource_type: FolderResourceType;
	resource_id: string;
}

/** Fusionne le contenu de plusieurs dossiers vers une cible (jamais d'écrasement). */
export async function mergeFolders(
	folderIds: string[],
	targetId: string,
	removeSources = false,
): Promise<FolderOperationReport> {
	return apiFetch<FolderOperationReport>("/v1/folders/merge", {
		method: "POST",
		body: JSON.stringify({
			folder_ids: folderIds,
			target_id: targetId,
			remove_sources: removeSources,
		}),
	});
}

/** Copy logique : ajoute les ressources à la cible SANS retirer les originaux. */
export async function copyResources(
	items: FolderResourceRef[],
	targetId: string,
): Promise<FolderOperationReport> {
	return apiFetch<FolderOperationReport>("/v1/folders/copy-resources", {
		method: "POST",
		body: JSON.stringify({ items, target_id: targetId }),
	});
}

/** Move logique : la cible devient l'unique dossier de chaque ressource. */
export async function moveResources(
	items: FolderResourceRef[],
	targetId: string,
): Promise<FolderOperationReport> {
	return apiFetch<FolderOperationReport>("/v1/folders/move-resources", {
		method: "POST",
		body: JSON.stringify({ items, target_id: targetId }),
	});
}

// ── Restore / Archive (extension consolidée) ─────────────────────────────────

/** Élément supprimé (soft delete) restituable. */
export interface DeletedItem {
	id: string;
	type: "folder" | "resource" | "document";
	name: string;
	deleted_at: string;
	deleted_by: string;
}

/** Liste les éléments supprimés (non purgés). */
export async function listDeletedItems(): Promise<DeletedItem[]> {
	return apiFetch<DeletedItem[]>("/v1/folders/deleted");
}

/** Restaure un élément supprimé. */
export async function restoreDeletedItem(itemId: string): Promise<void> {
	await apiFetch(`/v1/folders/deleted/${itemId}/restore`, { method: "POST" });
}

/** Vide définitivement la corbeille. */
export async function emptyTrash(): Promise<void> {
	await apiFetch("/v1/folders/deleted/empty", { method: "DELETE" });
}

/** Description d’un dossier à archiver. */
export interface ArchiveRequest {
	name: string;
	folder_ids: string[];
	format?: "zip" | "tar.gz" | "7z";
	compression_level?: number;
	include_metadata?: boolean;
	target_path?: string;
}

/** Réponse création d’archive (initialisation async). */
export interface ArchiveResponse {
	id: string;
	name: string;
	path: string;
	status: "pending" | "processing" | "ready" | "failed";
	file_count: number;
	size_bytes: number;
	created_at: string;
	format: string;
}

/** Planifie la création d'une archive consolidée. */
export async function createArchive(request: ArchiveRequest): Promise<ArchiveResponse> {
	return apiFetch<ArchiveResponse>("/v1/folders/archive", {
		method: "POST",
		body: JSON.stringify(request),
	});
}

/** Statut d’une archive (polling async). */
export async function getArchiveStatus(archiveId: string): Promise<ArchiveResponse> {
	return apiFetch<ArchiveResponse>(`/v1/folders/archive/${archiveId}`);
}
