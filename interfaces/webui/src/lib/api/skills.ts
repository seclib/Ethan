/**
 * ETHAN WebUI — Skills API service
 *
 * Maps Open-WebUI skills patterns to ETHAN API endpoints:
 *   OWUI: GET  /api/v1/skills          → ETHAN: GET  /v1/skills
 *   OWUI: POST /api/v1/skills           → ETHAN: POST /v1/skills
 *   OWUI: GET  /api/v1/skills/{id}     → ETHAN: GET  /v1/skills/{id}
 *   OWUI: POST /api/v1/skills/{id}/toggle → ETHAN: POST /v1/skills/{id}/toggle
 *
 * Skills are Core-owned (core/skills/store.py). The WebUI only displays and
 * sends actions.
 */

import { apiFetch } from '@/lib/api/client';

export interface Skill {
	id: string;
	name: string;
	description: string;
	content: string;
	version: string;
	status: string;
	is_active: boolean;
	tags: string[];
	meta: Record<string, unknown>;
	/** Modèle unifié : "prompt" (content → LLM) ou "pipeline" (steps → outils). */
	kind: 'prompt' | 'pipeline';
	steps: Array<Record<string, unknown>>;
	/** Outils (builtin/MCP) requis — validés par le Core à l'enregistrement. */
	required_tools: string[];
	valves: Record<string, unknown>;
	is_builtin: boolean;
	author: string;
	total_executions: number;
	success_count: number;
	last_run_at: string | null;
	created_at: string;
	updated_at: string;
}

/** List all skills */
export async function listSkills(): Promise<Skill[]> {
	return apiFetch<Skill[]>('/v1/skills');
}

/** Search skills */
export async function searchSkills(query: string): Promise<Skill[]> {
	return apiFetch<Skill[]>(`/v1/skills/search?q=${encodeURIComponent(query)}`);
}

/** Get a single skill */
export async function getSkill(id: string): Promise<Skill> {
	return apiFetch<Skill>(`/v1/skills/${id}`);
}

/** Create a skill (modèle unifié : prompt ou pipeline). */
export async function createSkill(data: {
	name: string;
	description?: string;
	content?: string;
	version?: string;
	tags?: string[];
	meta?: Record<string, unknown>;
	/** Discriminateur du modèle unifié : "prompt" (content → LLM) | "pipeline" (steps → outils). */
	kind?: 'prompt' | 'pipeline';
	steps?: Array<Record<string, unknown>>;
	/** Outils requis — validés par le Core au save (422 si inconnus). */
	required_tools?: string[];
	valves?: Record<string, unknown>;
	/** Toujours false pour une skill créée depuis un brouillon — aucune activation auto. */
	is_active?: boolean;
}): Promise<Skill> {
	return apiFetch<Skill>('/v1/skills', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Update a skill */
export async function updateSkill(id: string, data: Record<string, unknown>): Promise<Skill> {
	return apiFetch<Skill>(`/v1/skills/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

/** Delete a skill */
export async function deleteSkill(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/skills/${id}`, {
		method: 'DELETE',
	});
}

/** Toggle skill active state */
export async function toggleSkill(id: string): Promise<Skill> {
	return apiFetch<Skill>(`/v1/skills/${id}/toggle`, {
		method: 'POST',
	});
}

/** Execute a skill (builtins, moteur à étapes du SkillManager) */
export async function executeSkill(
	id: string,
	params: Record<string, unknown>,
): Promise<{ skill_id: string; status: string; result: unknown }> {
	return apiFetch<{ skill_id: string; status: string; result: unknown }>(
		`/v1/skills/${id}/execute`,
		{
			method: 'POST',
			body: JSON.stringify(params),
		},
	);
}

/** Run a catalogue skill via the ChatPipeline Core (moteur réel, contenu = instructions) */
export async function runSkill(
	id: string,
	input: string,
	opts?: { chat_id?: string; provider_id?: string; model?: string; user_id?: string },
): Promise<{ skill_id: string; status: string; chat_id: string; output: string; metadata: Record<string, unknown> }> {
	return apiFetch<{
		skill_id: string;
		status: string;
		chat_id: string;
		output: string;
		metadata: Record<string, unknown>;
	}>(`/v1/skills/${id}/run`, {
		method: 'POST',
		body: JSON.stringify({ input, ...opts }),
	});
}

/** Exporte toutes les skills (portabilité, pattern Open-WebUI). */
export async function exportSkills(): Promise<Skill[]> {
	return apiFetch<Skill[]>('/v1/skills/export');
}

/** Importe des skills exportées — nouvelles ids, jamais d'écrasement. */
export async function importSkills(
	records: Array<Record<string, unknown>>,
): Promise<{ imported: number; skipped: number }> {
	return apiFetch<{ imported: number; skipped: number }>('/v1/skills/import', {
		method: 'POST',
		body: JSON.stringify({ skills: records }),
	});
}

/**
 * Skill Lab (Core, sandbox Docker obligatoire — aucune exécution locale).
 * Exécution SYNCHRONE côté Core : la réponse est le résultat complet.
 * 503 si Docker est indisponible ; 422 si `code` est vide.
 */
export interface SkillLabResult {
	/** Identifiant Core du résultat (`lab_xxxx`) — présent dans l'historique. */
	id?: string;
	skill_name: string;
	status: string;
	passed: boolean;
	output: string;
	error: string;
	duration_ms: number;
	details: Record<string, unknown> | null;
	/** Horodatage Core du test (ISO 8601) — présent dans l'historique. */
	timestamp?: string;
}

export async function testSkillCode(
	code: string,
	opts?: { name?: string; input?: string; requirements?: string[] },
): Promise<SkillLabResult> {
	return apiFetch<SkillLabResult>('/v1/skills/lab/test', {
		method: 'POST',
		body: JSON.stringify({ code, ...opts }),
	});
}

/** Historique des résultats du Lab (optionnellement filtré par skill_name). */
export async function listSkillLabResults(
	skillName?: string,
): Promise<SkillLabResult[]> {
	const qs = skillName ? '?skill_name=' + encodeURIComponent(skillName) : '';
	return apiFetch<SkillLabResult[]>('/v1/skills/lab/results' + qs);
}
export interface SkillImportDetectionItem {
  source_path: string;
  name: string | null;
  status: string;
  errors: string[];
  description: string;
  version?: string | null;
  author?: string | null;
  tags?: string[];
  kind?: string | null;
  content_preview?: string;
  resources?: string[];
  checksum?: string;
  duplicate_status?: string;
  duplicate_of?: string;
  conflict_reason?: string;
  requires_classification?: boolean;
  suggested_target?: string;
}

export interface SkillImportSummary {
  expanded_files: number;
  detected_skills?: number;
  discovered?: number;
  imported?: number;
  skipped?: number;
  skipped_existing?: number;
  skipped_conflict?: number;
  invalid?: number;
  errors?: string[];
  conflicts?: Array<Record<string, unknown>>;
  imported_ids?: string[];
  items?: SkillImportDetectionItem[];
  ambiguous?: SkillImportDetectionItem[];
}


function selectSkillImportFiles(files: File[]): File[] {
  const normalize = (file: File) => (file.name || "").replace(/\\/g, "/").replace(/^\.\//, "");
  const skillRoots = new Set<string>();
  for (const file of files) {
    const relativePath = normalize(file);
    const segments = relativePath.split("/");
    if (segments[segments.length - 1].toUpperCase() === "SKILL.MD") {
      skillRoots.add(segments.slice(0, -1).join("/"));
    }
  }
  const isInsideSkill = (relativePath: string) =>
    [...skillRoots].some((root) => root === "" || relativePath === root || relativePath.startsWith(`${root}/`));
  return files.filter((file) => {
    const relativePath = normalize(file);
    const base = relativePath.split("/").pop() || "";
    if (isInsideSkill(relativePath)) return true;
    if (/\.mdx?$/i.test(base)) return true;
    if (/\.zip$/i.test(base)) return true;
    return false;
  });
}


export async function scanSkillImportFiles(files: File[]): Promise<SkillImportSummary> {
  const selectedFiles = selectSkillImportFiles(files);
  const formData = new FormData();
  for (const file of selectedFiles) {
    formData.append('files', file, file.name);
  }
  const response = await fetch('/api/v1/skills/import/scan', {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function importSkillFiles(
  files: File[],
  selected: string[] = [],
): Promise<SkillImportSummary> {
  const selectedFiles = selectSkillImportFiles(files);
  const formData = new FormData();
  for (const file of selectedFiles) {
    formData.append('files', file, file.name);
  }
  if (selected.length) {
    formData.append('selected', JSON.stringify(selected));
  }
  const response = await fetch('/api/v1/skills/import-files', {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail || `HTTP ${response.status}`);
  }
  return response.json();
}
