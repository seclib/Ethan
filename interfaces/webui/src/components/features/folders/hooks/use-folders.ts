"use client";

/**
 * Hooks Folders — couche d'organisation des ressources ETHAN.
 *
 * Passif par conception : toutes les mutations (créer, renommer, supprimer,
 * déplacer, classer) sont déléguées au Core via /v1/folders.  Ce hook ne
 * possède aucune logique métier — il invalide les caches react-query et
 * remonte les toasts.
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
	listFolderTree,
	createFolder as apiCreateFolder,
	updateFolder as apiUpdateFolder,
	moveFolder as apiMoveFolder,
	deleteFolder as apiDeleteFolder,
	getFolderIndex,
	type FolderTree,
	type FolderResourceType,
} from "@/lib/api/folders";
import { useUIStore } from "@/store/ui.store";

const TREE_KEY = ["folders-tree"];

export function useFolders() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	// ── Lectures ────────────────────────────────────────────────────────
	const {
		data: tree = [],
		isLoading: treeLoading,
		refetch: refetchTree,
	} = useQuery<FolderTree[]>({
		queryKey: TREE_KEY,
		queryFn: () => listFolderTree(),
		staleTime: 15_000,
	});

	// Index batch ressource → dossiers (filtrage des listes)
	const { data: folderIndex = {} } = useQuery<Record<string, string[]>>({
		queryKey: ["folders-index"],
		queryFn: () => getFolderIndex(),
		staleTime: 15_000,
	});

	// ── Mutations dossiers ──────────────────────────────────────────────
	const invalidate = () => {
		queryClient.invalidateQueries({ queryKey: TREE_KEY });
		queryClient.invalidateQueries({ queryKey: ["folders-index"] });
		queryClient.invalidateQueries({ queryKey: ["folder-resources"] });
	};

	const createFolderMutation = useMutation({
		mutationFn: (data: {
			name: string;
			parent_id?: string | null;
			description?: string;
			icon?: string | null;
		}) => apiCreateFolder(data),
		onSuccess: (folder) => {
			invalidate();
			addToast({ type: "success", message: `Dossier « ${folder.name} » créé` });
		},
		onError: (err: Error) => addToast({ type: "error", message: err.message }),
	});

	const updateFolderMutation = useMutation({
		mutationFn: ({
			folderId,
			data,
		}: {
			folderId: string;
			data: { name?: string; description?: string; icon?: string | null };
		}) => apiUpdateFolder(folderId, data),
		onSuccess: () => {
			invalidate();
			addToast({ type: "success", message: "Dossier mis à jour" });
		},
		onError: (err: Error) => addToast({ type: "error", message: err.message }),
	});

	const moveFolderMutation = useMutation({
		mutationFn: ({ folderId, parentId }: { folderId: string; parentId: string | null }) =>
			apiMoveFolder(folderId, parentId),
		onSuccess: () => {
			invalidate();
			addToast({ type: "success", message: "Dossier déplacé" });
		},
		onError: (err: Error) => addToast({ type: "error", message: err.message }),
	});

	const deleteFolderMutation = useMutation({
		mutationFn: (folderId: string) => apiDeleteFolder(folderId),
		onSuccess: () => {
			invalidate();
			addToast({ type: "success", message: "Dossier supprimé (ressources conservées)" });
		},
		onError: (err: Error) => addToast({ type: "error", message: err.message }),
	});

	return {
		tree,
		treeLoading,
		folderIndex,
		refetchTree,
		createFolder: createFolderMutation.mutate,
		updateFolder: updateFolderMutation.mutate,
		moveFolder: moveFolderMutation.mutate,
		deleteFolder: deleteFolderMutation.mutate,
		isMutating:
			createFolderMutation.isPending ||
			updateFolderMutation.isPending ||
			deleteFolderMutation.isPending ||
			moveFolderMutation.isPending,
	};
}

/** Sélection locale de navigation (dossier actif + filtre par type). */
export function useFoldersNavigation() {
	const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
	const [typeFilter, setTypeFilter] = useState<FolderResourceType | null>(null);
	const [showUntagged, setShowUntagged] = useState(false);
	return { selectedFolderId, setSelectedFolderId, typeFilter, setTypeFilter, showUntagged, setShowUntagged };
}