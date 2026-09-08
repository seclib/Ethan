/**
 * ETHAN WebUI — Library API service
 *
 * Unified library for documents, images, knowledge, project resources, and collections.
 * Uses Core APIs — does NOT create a duplicate storage system.
 *
 * Sources:
 *   Documents:  /v1/rag/documents, /v1/projects/{id}/documents
 *   Knowledge:  /v1/knowledge, /v1/knowledge/collections
 *   Images:     /v1/files (with image filter)
 *   Collections: /v1/knowledge/collections
 */

import { apiFetch } from '@/lib/api/client';

export type LibraryItemType = 'document' | 'image' | 'knowledge' | 'collection' | 'project';

export interface LibraryItem {
  id: string;
  title: string;
  type: LibraryItemType;
  description?: string;
  content?: string;
  source?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
  project_id?: string;
  collection_id?: string;
  size?: number;
  mime_type?: string;
  tags?: string[];
}

export interface LibraryFilters {
  type?: LibraryItemType | 'all';
  search?: string;
  sort_by?: 'title' | 'created_at' | 'updated_at' | 'type';
  sort_order?: 'asc' | 'desc';
  project_id?: string;
  collection_id?: string;
}

export interface LibraryResponse {
  items: LibraryItem[];
  total: number;
  filters: LibraryFilters;
}

// ── Documents (RAG) ──────────────────────────────────────────────────

export async function listRagDocuments(): Promise<LibraryItem[]> {
  const docs = await apiFetch<Array<Record<string, unknown>>>('/v1/rag/documents');
  return docs.map((d) => ({
    id: d.id as string,
    title: (d.title as string) || 'Untitled',
    type: 'document' as const,
    description: d.content as string,
    source: d.source as string,
    metadata: d.metadata as Record<string, unknown>,
    created_at: d.created_at as string,
  }));
}

// ── Knowledge Nodes ──────────────────────────────────────────────────

export async function listKnowledgeNodes(): Promise<LibraryItem[]> {
  const nodes = await apiFetch<Array<Record<string, unknown>>>('/v1/knowledge');
  return nodes.map((n) => ({
    id: n.id as string,
    title: (n.label as string) || 'Untitled',
    type: 'knowledge' as const,
    content: n.content as string,
    source: n.source as string,
    metadata: n.metadata as Record<string, unknown>,
    created_at: n.created_at as string,
    updated_at: n.updated_at as string,
  }));
}

// ── Knowledge Collections ────────────────────────────────────────────

export async function listCollections(): Promise<LibraryItem[]> {
  const cols = await apiFetch<Array<Record<string, unknown>>>('/v1/knowledge/collections');
  return cols.map((c) => ({
    id: c.id as string,
    title: (c.name as string) || 'Untitled',
    type: 'collection' as const,
    description: c.description as string,
    metadata: c.metadata as Record<string, unknown>,
    created_at: c.created_at as string,
    updated_at: c.updated_at as string,
  }));
}

// ── Project Documents ────────────────────────────────────────────────

export async function listProjectDocuments(projectId: string): Promise<LibraryItem[]> {
  const docs = await apiFetch<Array<Record<string, unknown>>>(`/v1/projects/${projectId}/documents`);
  return docs.map((d) => ({
    id: d.id as string,
    title: (d.title as string) || (d.filename as string) || 'Untitled',
    type: 'document' as const,
    source: d.source as string,
    metadata: d.metadata as Record<string, unknown>,
    created_at: d.created_at as string,
    project_id: projectId,
  }));
}

// ── Files (Images) ──────────────────────────────────────────────────

export async function listImageFiles(): Promise<LibraryItem[]> {
  const files = await apiFetch<Array<Record<string, unknown>>>('/v1/files');
  const imageTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/svg+xml'];
  return files
    .filter((f) => imageTypes.includes(f.mime_type as string))
    .map((f) => ({
      id: f.id as string,
      title: (f.name as string) || 'Untitled',
      type: 'image' as const,
      mime_type: f.mime_type as string,
      size: f.size as number,
      created_at: f.created_at as string,
    }));
}

// ── Unified Library ──────────────────────────────────────────────────

export async function getLibrary(filters: LibraryFilters = {}): Promise<LibraryResponse> {
  const items: LibraryItem[] = [];

  // Fetch from all sources based on filter
  const typeFilter = filters.type || 'all';

  try {
    if (typeFilter === 'all' || typeFilter === 'document') {
      if (filters.project_id) {
        items.push(...await listProjectDocuments(filters.project_id));
      } else {
        items.push(...await listRagDocuments());
      }
    }
  } catch {
    // Source unavailable, skip
  }

  try {
    if (typeFilter === 'all' || typeFilter === 'knowledge') {
      items.push(...await listKnowledgeNodes());
    }
  } catch {
    // Source unavailable, skip
  }

  try {
    if (typeFilter === 'all' || typeFilter === 'collection') {
      items.push(...await listCollections());
    }
  } catch {
    // Source unavailable, skip
  }

  try {
    if (typeFilter === 'all' || typeFilter === 'image') {
      items.push(...await listImageFiles());
    }
  } catch {
    // Source unavailable, skip
  }

  // Apply search filter
  let filtered = items;
  if (filters.search) {
    const searchLower = filters.search.toLowerCase();
    filtered = items.filter(
      (item) =>
        item.title.toLowerCase().includes(searchLower) ||
        item.description?.toLowerCase().includes(searchLower) ||
        item.content?.toLowerCase().includes(searchLower),
    );
  }

  // Apply sorting
  const sortBy = filters.sort_by || 'created_at';
  const sortOrder = filters.sort_order || 'desc';
  filtered.sort((a, b) => {
    const aVal = a[sortBy] || '';
    const bVal = b[sortBy] || '';
    const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
    return sortOrder === 'asc' ? cmp : -cmp;
  });

  return {
    items: filtered,
    total: filtered.length,
    filters,
  };
}
