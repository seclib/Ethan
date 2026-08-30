/**
 * ETHAN WebUI — Knowledge API service
 *
 * Maps Open-WebUI knowledge patterns to ETHAN API endpoints:
 *   OWUI: GET  /api/v1/knowledge          → ETHAN: GET  /v1/knowledge
 *   OWUI: POST /api/v1/knowledge           → ETHAN: POST /v1/knowledge
 *   OWUI: GET  /api/v1/knowledge/{id}     → ETHAN: GET  /v1/knowledge/{id}
 *   OWUI: POST /api/v1/knowledge/{id}/rag → ETHAN: POST /v1/knowledge/{id}/rag
 *   OWUI: GET  /api/v1/knowledge/{id}/file → ETHAN: GET  /v1/knowledge/collections/{id}/documents
 *
 * Collections are the ETHAN Core grouping of RAG documents.
 */

import { apiFetch } from '@/lib/api/client';

export interface KnowledgeNode {
	id: string;
	label: string;
	node_type: string;
	content: string;
	source: string;
	connections: Array<{
		id: string;
		to_node_id: string;
		relation_type: string;
		strength: number;
	}>;
	metadata: Record<string, unknown>;
	created_at: string;
	updated_at: string;
}

export interface KnowledgeCollection {
	id: string;
	name: string;
	description: string;
	user_id: string;
	document_ids: string[];
	metadata: Record<string, unknown>;
	created_at: string;
	updated_at: string;
}

export interface RagDocument {
	id: string;
	title: string;
	source: string;
	content: string;
	chunks: Array<{
		id: string;
		content: string;
		embedding: number[];
		document_id: string;
	}>;
	metadata: Record<string, unknown>;
	created_at: string;
}

/** List all knowledge nodes */
export async function listKnowledge(): Promise<KnowledgeNode[]> {
	return apiFetch<KnowledgeNode[]>('/v1/knowledge');
}

/** Search knowledge nodes */
export async function searchKnowledge(query: string): Promise<KnowledgeNode[]> {
	return apiFetch<KnowledgeNode[]>(`/v1/knowledge/search?q=${encodeURIComponent(query)}`);
}

/** Get a single knowledge node */
export async function getKnowledge(id: string): Promise<KnowledgeNode> {
	return apiFetch<KnowledgeNode>(`/v1/knowledge/${id}`);
}

/** Create a knowledge node */
export async function createKnowledge(data: {
	label: string;
	node_type?: string;
	content?: string;
	source?: string;
	connections?: Array<Record<string, unknown>>;
	metadata?: Record<string, unknown>;
}): Promise<KnowledgeNode> {
	return apiFetch<KnowledgeNode>('/v1/knowledge', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Ingest a knowledge node into RAG */
export async function ingestKnowledgeIntoRag(knowledgeId: string): Promise<{ knowledge_id: string; document_id: string }> {
	return apiFetch<{ knowledge_id: string; document_id: string }>(
		`/v1/knowledge/${knowledgeId}/rag`,
		{ method: 'POST' },
	);
}

// ── Collections ──────────────────────────────────────────────────────

/** List knowledge collections */
export async function listCollections(userId?: string): Promise<KnowledgeCollection[]> {
	const params = userId ? `?user_id=${encodeURIComponent(userId)}` : '';
	return apiFetch<KnowledgeCollection[]>(`/v1/knowledge/collections${params}`);
}

/** Create a knowledge collection */
export async function createCollection(data: {
	name: string;
	description?: string;
	user_id?: string;
	metadata?: Record<string, unknown>;
}): Promise<KnowledgeCollection> {
	return apiFetch<KnowledgeCollection>('/v1/knowledge/collections', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Get a collection */
export async function getCollection(id: string): Promise<KnowledgeCollection> {
	return apiFetch<KnowledgeCollection>(`/v1/knowledge/collections/${id}`);
}

/** Update a collection */
export async function updateCollection(id: string, data: Record<string, unknown>): Promise<KnowledgeCollection> {
	return apiFetch<KnowledgeCollection>(`/v1/knowledge/collections/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

/** Delete a collection */
export async function deleteCollection(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/knowledge/collections/${id}`, {
		method: 'DELETE',
	});
}

/** List documents in a collection */
export async function listCollectionDocuments(collectionId: string): Promise<RagDocument[]> {
	return apiFetch<RagDocument[]>(
		`/v1/knowledge/collections/${collectionId}/documents`,
	);
}

/** Add a document to a collection */
export async function addDocumentToCollection(
	collectionId: string,
	documentId: string,
): Promise<KnowledgeCollection> {
	return apiFetch<KnowledgeCollection>(
		`/v1/knowledge/collections/${collectionId}/documents`,
		{
			method: 'POST',
			body: JSON.stringify({ document_id: documentId }),
		},
	);
}

/** Remove a document from a collection */
export async function removeDocumentFromCollection(
	collectionId: string,
	documentId: string,
): Promise<KnowledgeCollection> {
	return apiFetch<KnowledgeCollection>(
		`/v1/knowledge/collections/${collectionId}/documents/${documentId}`,
		{ method: 'DELETE' },
	);
}

/** Retrieve chunks scoped to a collection */
export async function retrieveFromCollection(
	collectionId: string,
	query: string,
	topK?: number,
): Promise<Array<{ chunk: Record<string, unknown>; score: number; document_title: string; document_source: string }>> {
	return apiFetch<Array<{ chunk: Record<string, unknown>; score: number; document_title: string; document_source: string }>>(
		`/v1/knowledge/collections/${collectionId}/retrieve`,
		{
			method: 'POST',
			body: JSON.stringify({ query, top_k: topK }),
		},
	);
}

// ── RAG Documents ────────────────────────────────────────────────────

/** List all RAG documents */
export async function listRagDocuments(): Promise<RagDocument[]> {
	return apiFetch<RagDocument[]>('/v1/rag/documents');
}

/** Ingest a RAG document */
export async function ingestRagDocument(data: {
	content: string;
	title?: string;
	source?: string;
	metadata?: Record<string, unknown>;
}): Promise<RagDocument> {
	return apiFetch<RagDocument>('/v1/rag/documents', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Delete a RAG document */
export async function deleteRagDocument(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/rag/documents/${id}`, {
		method: 'DELETE',
	});
}

/**
 * Ingest an uploaded file (FileStore Core) into RAG.
 * Optionally attaches the created document to a Knowledge collection.
 * Maps to POST /v1/rag/documents/from-file/{file_id}
 */
export async function ingestFileIntoRag(
	fileId: string,
	opts?: { title?: string; collection_id?: string; force?: boolean },
): Promise<RagDocument & { attached_collection_id?: string | null }> {
	return apiFetch<RagDocument & { attached_collection_id?: string | null }>(
		`/v1/rag/documents/from-file/${fileId}`,
		{
			method: 'POST',
			body: JSON.stringify(opts ?? {}),
		},
	);
}
