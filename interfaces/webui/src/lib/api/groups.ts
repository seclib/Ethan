/**
 * ETHAN WebUI — Groups API service
 *
 * Thin gateway over ETHAN Core (core/auth/groups.py:GroupManager) via
 * interfaces/api/routers/domains.py /groups endpoints.  All business logic
 * (memberships, permission scopes, events) lives in the Core — this module
 * only serialises requests and deserialises responses.
 *
 * Admin gate: every mutating route requires Permission.ADMIN server-side.
 */

import { apiFetch } from '@/lib/api/client';

/** Sérialisation exacte de core/auth/groups.py:GroupManager → dict. */
export interface EthGroup {
  id: string;
  name: string;
  description: string;
  permissions: Record<string, unknown>;
  members: string[];
  metadata: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export async function listGroups(): Promise<EthGroup[]> {
  return apiFetch<EthGroup[]>('/groups');
}

export async function getGroup(groupId: string): Promise<EthGroup> {
  return apiFetch<EthGroup>(`/groups/${encodeURIComponent(groupId)}`);
}

export async function createGroup(data: {
  name: string;
  description?: string;
}): Promise<EthGroup> {
  return apiFetch<EthGroup>('/groups', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/** Champs supportés par GroupManager.update : name, description (permissions/metadata non exposés dans l'UI). */
export async function updateGroup(
  groupId: string,
  data: { name?: string; description?: string },
): Promise<EthGroup> {
  return apiFetch<EthGroup>(`/groups/${encodeURIComponent(groupId)}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteGroup(groupId: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/groups/${encodeURIComponent(groupId)}`, {
    method: 'DELETE',
  });
}

export async function addGroupMember(groupId: string, userId: string): Promise<EthGroup> {
  return apiFetch<EthGroup>(
    `/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}`,
    { method: 'POST' },
  );
}

export async function removeGroupMember(groupId: string, userId: string): Promise<EthGroup> {
  return apiFetch<EthGroup>(
    `/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}`,
    { method: 'DELETE' },
  );
}