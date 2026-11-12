import { apiFetch } from '@/lib/api/client';

export interface GitHubRepositoryRecord {
  organization: string;
  name: string;
  full_name: string;
  description: string | null;
  default_branch: string;
  html_url: string;
  clone_url: string;
  archived: boolean;
  visibility: string;
  updated_at: string | null;
  topics: string[];
}

export async function discoverGitHubOrganization(
  username: string,
): Promise<GitHubRepositoryRecord[]> {
  return apiFetch<GitHubRepositoryRecord[]>(
    `/v1/github/users/${encodeURIComponent(username)}/repositories`,
  );
}
