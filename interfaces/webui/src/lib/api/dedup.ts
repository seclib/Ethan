/**
 * ETHAN WebUI — Duplicate Detection API client.
 *
 * Passive layer: sends intents to the Core gateway (/v1/dedup).  All
 * classification and resolution logic lives in the Core (core/dedup); this
 * client only transmits user actions and renders reports.
 */

import { apiFetch } from '@/lib/api/client';

export type DuplicateCategory =
  | 'exact_duplicate'
  | 'probable_duplicate'
  | 'same_name_different_content'
  | 'different_version'
  | 'same_content_different_location'
  | 'already_indexed'
  | 'orphan_document'
  | 'broken_reference';

export type DuplicateAction =
  | 'keep_both'
  | 'replace_with_newest'
  | 'keep_primary'
  | 'move_to_archive'
  | 'delete_after_confirm'
  | 'repair_reference'
  | 'merge_associations';

export interface ScannedItem {
  id: string;
  domain: string;
  name: string;
  size: number;
  content_type: string;
  content_hash: string;
  created_at: string;
  updated_at: string;
  locations: string[];
  project_ids: string[];
  collection_ids: string[];
  folder_ids: string[];
  rag_document_id: string;
  metadata: Record<string, unknown>;
}

export interface DuplicateGroup {
  group_id: string;
  category: DuplicateCategory;
  items: ScannedItem[];
  confidence: number;
  recommended_action: DuplicateAction;
}

export interface DuplicateReport {
  scan_id: string;
  timestamp: string;
  total_scanned: number;
  total_files: number;
  total_project_documents: number;
  total_knowledge_nodes: number;
  total_rag_documents: number;
  groups: DuplicateGroup[];
  orphans: ScannedItem[];
  broken_references: ScannedItem[];
}

export interface ResolutionResult {
  group_id: string;
  action: DuplicateAction;
  status: 'pending' | 'applied' | 'failed' | 'needs_confirm';
  needs_confirmation: boolean;
  message: string;
  affected_items: string[];
  kept_item_id: string;
  removed_item_ids: string[];
  associations: Record<string, string[]>;
  locations: string[];
  rag_document_ids: string[];
  project_ids: string[];
  collection_ids: string[];
  error: string;
}

export interface CategoriesResponse {
  categories: DuplicateCategory[];
  actions: DuplicateAction[];
}

export async function scanDuplicates(userId?: string): Promise<DuplicateReport> {
  return apiFetch<DuplicateReport>('/v1/dedup/scan', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId ?? null }),
  });
}

export async function getDuplicateReport(scanId: string): Promise<DuplicateReport> {
  return apiFetch<DuplicateReport>(`/v1/dedup/report/${scanId}`);
}

export async function getDedupCategories(): Promise<CategoriesResponse> {
  return apiFetch<CategoriesResponse>('/v1/dedup/categories');
}

export async function resolveDuplicateGroup(
  groupId: string,
  action: DuplicateAction,
  confirmed = false,
  primaryItemId = '',
): Promise<ResolutionResult> {
  return apiFetch<ResolutionResult>('/v1/dedup/resolve', {
    method: 'POST',
    body: JSON.stringify({
      group_id: groupId,
      action,
      confirmed,
      primary_item_id: primaryItemId,
    }),
  });
}
