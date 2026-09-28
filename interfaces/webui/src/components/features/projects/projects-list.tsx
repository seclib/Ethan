"use client";

/**
 * ProjectsList — inventaire des Projects de l'utilisateur.
 *
 * Le WebUI est un client passif : la liste et les mutations délèguent au
 * ProjectManager Core (/v1/projects). Chaque projet ouvre son workspace.
 */

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FolderKanban, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import { useProjectsStore } from "@/lib/store/projects";
import { useUIStore } from "@/store/ui.store";

export function ProjectsList() {
  const router = useRouter();
  const addToast = useUIStore((s) => s.addToast);
  const projects = useProjectsStore((s) => s.projects);
  const loading = useProjectsStore((s) => s.loading);
  const loadProjects = useProjectsStore((s) => s.loadProjects);
  const createProject = useProjectsStore((s) => s.createProject);

  const [showCreate, setShowCreate] = React.useState(false);
  const [name, setName] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  const handleCreate = async () => {
    if (!name.trim() || submitting) return;
    setSubmitting(true);
    try {
      // createProject active automatiquement le projet (store Core-backed).
      const project = await createProject({ name: name.trim() });
      setShowCreate(false);
      setName("");
      router.push(`/projects/${project.id}`);
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to create project",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-4 overflow-y-auto p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">Projects</h1>
          <p className="text-sm text-muted-foreground">
            Un Project regroupe des conversations autour d&apos;un contexte
            (instructions, connaissances, fichiers, agent et modèle par défaut).
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          New project
        </Button>
      </div>

      {loading && projects.length === 0 ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : projects.length === 0 ? (
        <div className="rounded-lg border border-line-1/60 p-8 text-center">
          <FolderKanban className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">
            Aucun projet pour le moment. Créez-en un pour scoper vos conversations.
          </p>
        </div>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {projects.map((project) => (
            <li key={project.id}>
              <Link
                href={`/projects/${project.id}`}
                className="block rounded-lg border border-line-1/60 p-4 transition-colors hover:bg-accent"
              >
                <div className="flex items-center gap-2">
                  <FolderKanban className="h-4 w-4 text-muted-foreground" />
                  <span className="truncate font-medium">{project.name}</span>
                </div>
                {project.description && (
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                    {project.description}
                  </p>
                )}
                <p className="mt-2 text-xs text-muted-foreground">
                  {(project.knowledge_ids?.length ?? 0)} knowledge ·{" "}
                  {(project.skill_ids?.length ?? 0)} skills ·{" "}
                  {(project.tool_ids?.length ?? 0)} tools
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <Dialog open={showCreate} title="Create Project" onClose={() => setShowCreate(false)}>
        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="new-project-name">Project Name</label>
            <Input
              id="new-project-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., OSINT Research"
              disabled={submitting}
            />
          </div>
          <p className="text-sm text-muted-foreground">
            Le projet sera activé immédiatement : vos prochaines conversations
            s&apos;exécuteront dans son contexte.
          </p>
        </div>
        <div className="flex justify-end gap-2 border-t pt-4">
          <Button variant="outline" size="sm" onClick={() => setShowCreate(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={() => void handleCreate()} disabled={!name.trim() || submitting}>
            {submitting ? "Creating…" : "Create"}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
