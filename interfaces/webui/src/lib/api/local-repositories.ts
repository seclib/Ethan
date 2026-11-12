import { apiFetch } from '@/lib/api/client';

export interface LocalRepositoryAnalysis {
  path: string;
  name: string;
  branch: string | null;
  head: string | null;
  remote: string | null;
  working_tree_status: string;
  changed_files: number;
  detected_files: string[];
  classification: string;
}

export async function listLocalRepositories(): Promise<LocalRepositoryAnalysis[]> {
  return apiFetch<LocalRepositoryAnalysis[]>('/v1/local-repositories');
}
