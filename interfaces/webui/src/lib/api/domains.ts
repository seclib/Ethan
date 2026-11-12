/**
 * ETHAN WebUI — Domains API service
 *
 * Client passif des domains de spécialité Core (/v1/domains).  Toute la
 * logique (domains, memberships many-to-many, résolution des ressources)
 * appartient au Core (core/domains) : cette couche n'affiche et ne transmet
 * que des intentions utilisateur.
 */

import { apiFetch } from '@/lib/api/client';

export type DomainResourceType = "knowledge" | "collection" | "skill";

export interface Domain {
	id: string;
	name: string;
	description: string;
	user_id: string;
	icon: string | null;
	color: string | null;
	order: number;
	metadata: Record<string, unknown>;
	created_at: string;
	updated_at: string;
}

export interface DomainWithCount extends Domain {
	/** Nombre de ressources rattachées au domain. */
	resource_count: number;
}

export interface DomainResource {
	resource_type: DomainResourceType;
	resource_id: string;
	/** Record réel résolu par le manager Core propriétaire. */
	record: Record<string, unknown> | null;
}

export async function listDomains(userId?: string): Promise<DomainWithCount[]> {
	const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
	return apiFetch<DomainWithCount[]>(`/v1/domains${query}`);
}

export async function getDomain(domainId: string): Promise<Domain> {
	return apiFetch<Domain>(`/v1/domains/${domainId}`);
}

export async function createDomain(data: {
	name: string;
	description?: string;
	user_id?: string;
	icon?: string | null;
	color?: string | null;
	order?: number;
}): Promise<Domain> {
	return apiFetch<Domain>("/v1/domains", {
		method: "POST",
		body: JSON.stringify(data),
	});
}

export async function updateDomain(
	domainId: string,
	data: {
		name?: string;
		description?: string;
		icon?: string | null;
		color?: string | null;
		order?: number;
	},
): Promise<Domain> {
	return apiFetch<Domain>(`/v1/domains/${domainId}`, {
		method: "PATCH",
		body: JSON.stringify(data),
	});
}

export async function deleteDomain(domainId: string): Promise<void> {
	await apiFetch(`/v1/domains/${domainId}`, { method: "DELETE" });
}

export async function listDomainResources(
	domainId: string,
	resourceType?: DomainResourceType,
): Promise<DomainResource[]> {
	const query = resourceType ? `?resource_type=${resourceType}` : "";
	return apiFetch<DomainResource[]>(`/v1/domains/${domainId}/resources${query}`);
}

export async function attachDomainResource(
	domainId: string,
	resourceType: DomainResourceType,
	resourceId: string,
): Promise<void> {
	await apiFetch(`/v1/domains/${domainId}/resources`, {
		method: "POST",
		body: JSON.stringify({ resource_type: resourceType, resource_id: resourceId }),
	});
}

export async function detachDomainResource(
	domainId: string,
	resourceType: DomainResourceType,
	resourceId: string,
): Promise<void> {
	await apiFetch(
		`/v1/domains/${domainId}/resources/${resourceType}/${resourceId}`,
		{ method: "DELETE" },
	);
}

/** Domains contenant une ressource (multi-membership possible). */
export async function listDomainsOfResource(
	resourceType: DomainResourceType,
	resourceId: string,
): Promise<Domain[]> {
	return apiFetch<Domain[]>(
		`/v1/domains/by-resource/${resourceType}/${resourceId}`,
	);
}

/** Index batch `{resource_id: [domain_id, ...]}` — filtrage des listes par domain. */
export async function getDomainIndex(
	resourceType?: DomainResourceType,
): Promise<Record<string, string[]>> {
	const query = resourceType ? `?resource_type=${resourceType}` : "";
	return apiFetch<Record<string, string[]>>(`/v1/domains/index${query}`);
}
