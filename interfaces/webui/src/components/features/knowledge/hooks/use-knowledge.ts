"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
	listKnowledge,
	searchKnowledge,
	listCollections,
	createCollection as apiCreateCollection,
	updateCollection as apiUpdateCollection,
	deleteCollection as apiDeleteCollection,
	listRagDocuments,
	ingestRagDocument,
	deleteRagDocument,
	listCollectionDocuments as apiListCollectionDocuments,
	addDocumentToCollection as apiAddDocumentToCollection,
	removeDocumentFromCollection as apiRemoveDocumentFromCollection,
	retrieveFromCollection as apiRetrieveFromCollection,
	type KnowledgeNode,
	type KnowledgeCollection,
	type RagDocument,
} from "@/lib/api/knowledge";
import { useUIStore } from "@/store/ui.store";
import { useState } from "react";

export function useKnowledge() {
	const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	// Knowledge graph nodes
	const { data: nodes = [], isLoading, error, refetch } = useQuery<KnowledgeNode[]>({
		queryKey: ["knowledgeNodes"],
		queryFn: () => listKnowledge() as Promise<KnowledgeNode[]>,
		staleTime: 30_000,
	});

	// Knowledge collections (grouping of RAG documents)
	const { data: collections = [], refetch: refetchCollections } = useQuery<KnowledgeCollection[]>({
		queryKey: ["knowledgeCollections"],
		queryFn: () => listCollections(),
		staleTime: 30_000,
	});

	// RAG documents catalogue
	const { data: documents = [] } = useQuery<RagDocument[]>({
		queryKey: ["ragDocuments"],
		queryFn: () => listRagDocuments(),
		staleTime: 30_000,
	});

	const createCollectionMutation = useMutation({
		mutationFn: ({ name, description }: { name: string; description?: string }) =>
			apiCreateCollection({ name, description }),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["knowledgeCollections"] });
			addToast({ type: "success", message: "Collection created" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to create collection" });
		},
	});

	const updateCollectionMutation = useMutation({
		mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
			apiUpdateCollection(id, data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["knowledgeCollections"] });
			addToast({ type: "success", message: "Collection updated" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to update collection" });
		},
	});

	const addDocumentMutation = useMutation({
		mutationFn: ({ collectionId, documentId }: { collectionId: string; documentId: string }) =>
			apiAddDocumentToCollection(collectionId, documentId),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["knowledgeCollections"] });
			addToast({ type: "success", message: "Document added to collection" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to add document" });
		},
	});

	const removeDocumentMutation = useMutation({
		mutationFn: ({ collectionId, documentId }: { collectionId: string; documentId: string }) =>
			apiRemoveDocumentFromCollection(collectionId, documentId),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["knowledgeCollections"] });
			addToast({ type: "success", message: "Document removed from collection" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to remove document" });
		},
	});

	const deleteCollectionMutation = useMutation({
		mutationFn: (id: string) => apiDeleteCollection(id),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["knowledgeCollections"] });
			addToast({ type: "success", message: "Collection deleted" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to delete collection" });
		},
	});

	const ingestDocumentMutation = useMutation({
		mutationFn: (data: { content: string; title?: string; source?: string }) =>
			ingestRagDocument(data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["ragDocuments"] });
			addToast({ type: "success", message: "Document ingested into RAG" });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to ingest document" });
		},
	});

	const createCollection = (name: string, description?: string) =>
		createCollectionMutation.mutate({ name, description });

	const deleteCollection = (id: string) => deleteCollectionMutation.mutate(id);

	const updateCollection = (id: string, data: Record<string, unknown>) =>
		updateCollectionMutation.mutate({ id, data });

	const addDocumentToCollection = (collectionId: string, documentId: string) =>
		addDocumentMutation.mutate({ collectionId, documentId });

	const removeDocumentFromCollection = (collectionId: string, documentId: string) =>
		removeDocumentMutation.mutate({ collectionId, documentId });

	const ingestDocument = (data: { content: string; title?: string; source?: string }) =>
		ingestDocumentMutation.mutate(data);

	const listCollectionDocuments = async (collectionId: string) => {
		return apiListCollectionDocuments(collectionId);
	};

	const retrieveFromCollection = async (collectionId: string, query: string, topK?: number) => {
		return apiRetrieveFromCollection(collectionId, query, topK);
	};

	return {
		nodes,
		selectedNode,
		collections,
		documents,
		isLoading,
		error: error instanceof Error ? error.message : null,
		fetchNodes: refetch,
		searchNodes: async (query: string) => {
			const results = await searchKnowledge(query) as KnowledgeNode[];
			return results;
		},
		selectNode: setSelectedNode,
		createCollection,
		deleteCollection,
		updateCollection,
		addDocumentToCollection,
		removeDocumentFromCollection,
		listCollectionDocuments,
		retrieveFromCollection,
		ingestDocument,
	};
}