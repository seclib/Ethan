/**
 * ETHAN WebUI — Search API service
 *
 * Maps to ETHAN API endpoints:
 *   GET /v1/search?q=...&type=...&limit=...  → search()
 *   GET /v1/search/types                      → listSearchTypes()
 *
 * Four search types: web, knowledge, library, conversation
 */

import { apiFetch } from '@/lib/api/client';

export type SearchType = 'web' | 'knowledge' | 'library' | 'conversation';

export interface SearchResult {
  id: string;
  title: string;
  content?: string;
  source?: string;
  type: string;
  score?: number;
  created_at?: string;
  match_in?: string;
  description?: string;
  document_count?: number;
  chat_id?: string;
}

export interface SearchResponse {
  query: string;
  type: SearchType;
  results: SearchResult[];
  total: number;
  error?: string;
}

export async function search(
  query: string,
  type: SearchType = 'knowledge',
  limit: number = 20,
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, type, limit: String(limit) });
  return apiFetch<SearchResponse>(`/v1/search?${params.toString()}`);
}

export async function listSearchTypes(): Promise<{ types: string[] }> {
  return apiFetch<{ types: string[] }>('/v1/search/types');
}
