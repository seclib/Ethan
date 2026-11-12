"use client";

/**
 * Hooks classement — contenu des dossiers et mutations de ressources.
 *
 * Le contenu d'un dossier est résolu par le Core (providers vers les managers
 * propriétaires) ; ce module ne fait que l'afficher et transmettre les
 * intentions utilisateur (classer, déplacer, retirer).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
	listFolderResources,
	attachFolderResource,
	detachFolderResource,
	moveResource as apiMoveResource,
	listUntaggedResources,
	listFoldersOfResource,
	type Folder,
	type FolderResource,
	type FolderResourceType,
} from "@/lib/api/folders";
import { useUIStore } from "@/store/ui.store";

const TREE_KEY = ["folders-tree"];

/** Contenu d'un dossier (ressources réelles résolues par le Core). */
export function useFolderResources(folderId: string | null) {
	return useQuery<FolderResource[]>({
		queryKey: ["folder-resources", folderId],
		queryFn: () => listFolderResources(folderId as string),
		enabled: folderId !== null,
		staleTime: 15_000,
	});
}

/** Ressources d'un type classées dans aucun dossier. */
export function useUntaggedResources(resourceType: FolderResourceType | null) {
	return useQuery<Record<string, unknown>[]>({
		queryKey: ["folders-untagged", resourceType],
		queryFn: () => listUntaggedResources(resourceType as FolderResourceType),
		enabled: resourceType !== null,
		staleTime: 15_000,
	});
}

/** Dossiers d'une ressource (pour le dialog de classement multi-dossiers). */
export function useResourceFolders(
	resourceType: FolderResourceType | null,
	resourceId: string | null,
) {
	return useQuery<Folder[]>({
		queryKey: ["folders-of-resource", resourceType, resourceId],
		queryFn: () =>
			listFoldersOfResource(resourceType as FolderResourceType, resourceId as string),
		enabled: resourceType !== null && resourceId !== null,
		staleTime: 10_000,
	});
}

/** Mutations de classement des ressources (attach/detach/move). */
export function useResourceClassification() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	const invalidate = () => {
		queryClient.invalidateQueries({ queryKey: TREE_KEY });
		queryClient.invalidateQueries({ queryKey: ["folders-index"] });
		queryClient.invalidateQueries({ queryKey: ["folder-resources"] });
		queryClient.invalidateQueries({ queryKey: ["folders-untagged"] });
		queryClient.invalidateQueries({ queryKey: ["folders-of-resource"] });
	};

	const attachMutation = useMutation({
		mutationFn: (data: {
			folderId: string;
			resourceType: FolderResourceType;
			resourceId: string;
		}) => attachFolderResource(data.folderId, data.resourceType, data.resourceId),
		onSuccess: () => {
			invalidate();
			addToast({ type: "success", message: "Ressource classée" });
		},
		onError: (err: Error) => addToast({ type: "error", message: err.message }),
	});

	const detachMutation = useMutation({
		mutationFn: (data: {
			folderId: string;
			resourceType: FolderResourceType;
			resourceId: string;
		}) => detachFolderResource(data.folderId, data.resourceType, data.resourceId),
		onSuccess: () => {
			invalidate();
			addToast({ type: "success", message: "Ressource retirée du dossier" });
		},
		onError: (err: Error) => addToast({ type: "error", message: err.message }),
	});

	const moveMutation = useMutation({
		mutationFn: (data: {
			resourceType: FolderResourceType;
			resourceId: string;
			folderIds: string[];
		}) => apiMoveResource(data.resourceType, data.resourceId, data.folderIds),
		onSuccess: () => {
			invalidate();
			addToast({ type: "success", message: "Ressource déplacée" });
		},
		onError: (err: Error) => addToast({ type: "error", message: err.message }),
	});

	return {
		attachResource: attachMutation.mutate,
		detachResource: detachMutation.mutate,
		moveResource: moveMutation.mutate,
		isMutating: attachMutation.isPending || detachMutation.isPending || moveMutation.isPending,
	};
}