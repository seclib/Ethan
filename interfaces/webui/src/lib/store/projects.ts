/**
 * ETHAN WebUI — Projects store (Zustand)
 *
 * Centralised UI state for Projects.
 *   - active project (id + context from Core)
 *   - list of user's projects
 *   - loading/error states
 *
 * WebUI stays a pure client: every mutation delegates to core/projects
 * via the /v1/projects* endpoints.
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import {
	listProjects,
	getProject,
	createProject,
	updateProject,
	deleteProject,
	selectProject,
	type Project,
	type ProjectSelection,
} from '@/lib/api/projects';
import { ProjectContext } from '@/lib/api/projects';

export interface ProjectState {
	projects: Project[];
	activeProject: Project | null;
	activeContext: ProjectContext | null;
	loading: boolean;
	error: string | null;
	/** Load all projects for the current user. */
	loadProjects: () => Promise<void>;
	/** Create + switch to a new project. */
	createProject: (data: Partial<Project>) => Promise<Project>;
	/** Update a project (optimistic on the list). */
	updateProject: (id: string, data: Partial<Project>) => Promise<Project>;
	/** Delete a project. */
	deleteProject: (id: string) => Promise<void>;
	/** Select / switch the active project. */
	setActiveProject: (id: string | null) => Promise<void>;
	/** Refresh active project context from Core. */
	refreshActiveContext: () => Promise<void>;
	/** Clear errors. */
	clearError: () => void;
}

export const useProjectsStore = create<ProjectState>()(
	devtools(
		(set, get) => ({
			projects: [],
			activeProject: null,
			activeContext: null,
			loading: false,
			error: null,

			clearError: () => set({ error: null }),

			loadProjects: async () => {
				set({ loading: true, error: null });
				try {
					const projects = await listProjects();
					set({ projects, loading: false });
				} catch (err: any) {
					set({ error: err.message, loading: false });
				}
			},

			createProject: async (data) => {
				set({ loading: true, error: null });
				try {
					const project = await createProject(data);
					set((s) => ({
						projects: [...s.projects, project],
						loading: false,
					}));
					return project;
				} catch (err: any) {
					set({ error: err.message, loading: false });
					throw err;
				}
			},

			updateProject: async (id, data) => {
				set({ loading: true, error: null });
				try {
					const updated = await updateProject(id, data);
					set((s) => ({
						projects: s.projects.map((p) => (p.id === id ? updated : p)),
						activeProject: s.activeProject?.id === id ? updated : s.activeProject,
						loading: false,
					}));
					return updated;
				} catch (err: any) {
					set({ error: err.message, loading: false });
					throw err;
				}
			},

			deleteProject: async (id) => {
				set({ loading: true, error: null });
				try {
					await deleteProject(id);
					set((s) => ({
						projects: s.projects.filter((p) => p.id !== id),
						activeProject: s.activeProject?.id === id ? null : s.activeProject,
						activeContext: s.activeProject?.id === id ? null : s.activeContext,
						loading: false,
					}));
				} catch (err: any) {
					set({ error: err.message, loading: false });
					throw err;
				}
			},

			setActiveProject: async (id) => {
				set({ loading: true, error: null });
				try {
					await selectProject(id);
					if (id) {
						const project = await getProject(id);
						set({ activeProject: project, loading: false });
						await get().refreshActiveContext();
					} else {
						set({ activeProject: null, activeContext: null, loading: false });
					}
				} catch (err: any) {
					set({ error: err.message, loading: false });
					throw err;
				}
			},

			refreshActiveContext: async () => {
				const active = get().activeProject;
				if (!active?.id) {
					set({ activeContext: null });
					return;
				}
				// Context is carried alongside the project record from Core.
				set({
					activeContext: {
						id: active.id,
						name: active.name,
						instructions: active.instructions,
						agent_id: active.agent_id,
						provider_id: active.provider_id,
						model: active.model,
						folder_ids: active.folder_ids,
						knowledge_ids: active.knowledge_ids,
						collection_ids: active.collection_ids,
						skill_ids: active.skill_ids,
						tool_ids: active.tool_ids,
					},
				});
			},
		}),
		{ name: 'ethan-projects-store' },
	),
);
