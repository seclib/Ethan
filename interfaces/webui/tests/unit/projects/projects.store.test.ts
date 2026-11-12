/**
 * Tests — store Projects (Zustand) : sélection active, persistance locale,
 * restauration après refresh, purge si le projet n'existe plus.
 *
 * Le store est un client pur : toutes les mutations délèguent aux API Core
 * (/v1/projects) — ici mockées pour isoler la logique d'état d'interface.
 */

import { useProjectsStore } from "@/lib/store/projects";
import * as projectsApi from "@/lib/api/projects";
import type { Project } from "@/lib/api/projects";

// Le store ne parle qu'aux API Core : module entièrement mocké (aucun réseau).
jest.mock("@/lib/api/projects");

const STORAGE_KEY = "ethan.activeProjectId";

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: "p1",
    name: "Recon",
    description: "",
    instructions: "",
    user_id: "alice",
    folder_ids: [],
    knowledge_ids: [],
    collection_ids: [],
    skill_ids: [],
    tool_ids: [],
    metadata: {},
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    ...overrides,
  };
}

const mocked = projectsApi as jest.Mocked<typeof projectsApi>;

describe("Projects store — sélection et persistance", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.localStorage.clear();
    useProjectsStore.setState({
      projects: [],
      activeProject: null,
      activeContext: null,
      loading: false,
      error: null,
    });
  });

  it("setActiveProject persiste la sélection et résout le contexte Core", async () => {
    const project = makeProject();
    mocked.selectProject.mockResolvedValue({ active_project_id: project.id });
    mocked.getProject.mockResolvedValue(project);

    await useProjectsStore.getState().setActiveProject(project.id);

    expect(mocked.selectProject).toHaveBeenCalledWith(project.id);
    expect(useProjectsStore.getState().activeProject?.id).toBe(project.id);
    expect(useProjectsStore.getState().activeContext?.name).toBe(project.name);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe(project.id);
  });

  it("setActiveProject(null) efface la sélection persistée", async () => {
    window.localStorage.setItem(STORAGE_KEY, "p1");
    mocked.selectProject.mockResolvedValue({ active_project_id: null });

    await useProjectsStore.getState().setActiveProject(null);

    expect(useProjectsStore.getState().activeProject).toBeNull();
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it("createProject ajoute le projet ET l'active (UX chat immédiate)", async () => {
    const project = makeProject({ id: "p-new", name: "Nouveau" });
    mocked.createProject.mockResolvedValue(project);
    mocked.selectProject.mockResolvedValue({ active_project_id: project.id });
    mocked.getProject.mockResolvedValue(project);

    const created = await useProjectsStore.getState().createProject({ name: "Nouveau" });

    expect(created.id).toBe(project.id);
    expect(useProjectsStore.getState().projects).toHaveLength(1);
    expect(useProjectsStore.getState().activeProject?.id).toBe(project.id);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe(project.id);
  });

  it("restoreActiveProject restaure la préférence persistée", async () => {
    const project = makeProject({ id: "p-restored" });
    window.localStorage.setItem(STORAGE_KEY, project.id);
    mocked.selectProject.mockResolvedValue({ active_project_id: project.id });
    mocked.getProject.mockResolvedValue(project);

    await useProjectsStore.getState().restoreActiveProject();

    expect(useProjectsStore.getState().activeProject?.id).toBe(project.id);
  });

  it("restoreActiveProject purge la préférence si le projet n'existe plus", async () => {
    window.localStorage.setItem(STORAGE_KEY, "deleted-project");
    mocked.selectProject.mockResolvedValue({ active_project_id: "deleted-project" });
    mocked.getProject.mockRejectedValue(new Error("Project deleted-project not found"));

    await useProjectsStore.getState().restoreActiveProject();

    expect(useProjectsStore.getState().activeProject).toBeNull();
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it("deleteProject retire le projet et purge la sélection s'il était actif", async () => {
    const project = makeProject({ id: "p-del" });
    mocked.deleteProject.mockResolvedValue({ status: "deleted" });
    useProjectsStore.setState({
      projects: [project],
      activeProject: project,
    });
    window.localStorage.setItem(STORAGE_KEY, project.id);

    await useProjectsStore.getState().deleteProject(project.id);

    expect(useProjectsStore.getState().projects).toHaveLength(0);
    expect(useProjectsStore.getState().activeProject).toBeNull();
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();
  });
});
