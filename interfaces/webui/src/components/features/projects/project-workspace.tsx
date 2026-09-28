"use client";

/**
 * ProjectWorkspace — cockpit d'un Project ETHAN.
 *
 * Quatre vues : Instructions · Fichiers · Conversations · Configuration.
 * Le WebUI reste un client passif : chaque action délègue au Core
 * (ProjectManager, ChatStore, pipeline RAG) via /v1/projects* et /chats.
 * Aucune logique métier ni état métier persistant côté interface.
 */

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  FileText,
  MessageSquarePlus,
  MessagesSquare,
  Settings2,
  SlidersHorizontal,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { FileUploadDropzone } from "./file-upload-dropzone";
import { ProjectFilesTable } from "./project-files-table";
import { apiFetch } from "@/lib/api/client";
import { createChat } from "@/lib/api/chat";
import { getProject, type Project, type ProjectPatch } from "@/lib/api/projects";
import { listAgents } from "@/lib/api/agents";
import { listCollections, type KnowledgeCollection } from "@/lib/api/knowledge";
import { listProviders, type Provider } from "@/lib/api/providers";
import { listSkills, type Skill } from "@/lib/api/skills";
import { listTools, type CoreTool } from "@/lib/api/tools";
import { useProjectsStore } from "@/lib/store/projects";
import { useChatSidebarStore } from "@/store/chat-sidebar.store";
import { useUIStore } from "@/store/ui.store";
import type { Agent } from "@/types";

type TabId = "instructions" | "files" | "conversations" | "configuration";

const TABS: Array<{ id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: "instructions", label: "Instructions", icon: SlidersHorizontal },
  { id: "files", label: "Fichiers", icon: FileText },
  { id: "conversations", label: "Conversations", icon: MessagesSquare },
  { id: "configuration", label: "Configuration", icon: Settings2 },
];

/** Conversation minimale affichée dans l'onglet Conversations (source : /chats). */
interface ChatSummary {
  id: string;
  title: string;
  updated_at: string;
}

const SELECT_CLASS =
  "rounded-md border border-line-1 bg-background px-3 py-2 text-sm text-foreground disabled:opacity-50";

export function ProjectWorkspace({ projectId }: { projectId: string }) {
  const router = useRouter();
  const addToast = useUIStore((s) => s.addToast);
  const updateProjectInStore = useProjectsStore((s) => s.updateProject);
  const deleteProjectInStore = useProjectsStore((s) => s.deleteProject);
  const setActiveProject = useProjectsStore((s) => s.setActiveProject);
  const setPendingChat = useChatSidebarStore((s) => s.setPendingChat);

  const [project, setProject] = React.useState<Project | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const [activeTab, setActiveTab] = React.useState<TabId>("instructions");
  const [saving, setSaving] = React.useState(false);
  const [confirmDelete, setConfirmDelete] = React.useState(false);
  /** Clé de rafraîchissement de l'onglet Fichiers (upload/suppression). */
  const [filesRefreshKey, setFilesRefreshKey] = React.useState(0);

  // Formulaire Instructions (état local d'édition — la vérité reste au Core).
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [instructions, setInstructions] = React.useState("");

  // Conversations du projet (ChatStore Core, scope project_id).
  const [chats, setChats] = React.useState<ChatSummary[]>([]);
  const [chatsLoading, setChatsLoading] = React.useState(false);
  const [creatingChat, setCreatingChat] = React.useState(false);

  // Catalogue Configuration (chargé à la demande, source : Core).
  const [providers, setProviders] = React.useState<Provider[]>([]);
  const [agents, setAgents] = React.useState<Agent[]>([]);
  const [collections, setCollections] = React.useState<KnowledgeCollection[]>([]);
  const [skills, setSkills] = React.useState<Skill[]>([]);
  const [tools, setTools] = React.useState<CoreTool[]>([]);
  const [catalogLoaded, setCatalogLoaded] = React.useState(false);

  /** Recharge le Project depuis le Core (source de vérité unique). */
  const loadProject = React.useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const record = await getProject(projectId);
      setProject(record);
      setName(record.name ?? "");
      setDescription(record.description ?? "");
      setInstructions(record.instructions ?? "");
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load project");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  React.useEffect(() => {
    void loadProject();
  }, [loadProject]);


  // ── Conversations du projet (scope Core : /chats?project_id=…) ──────────
  const loadChats = React.useCallback(async () => {
    setChatsLoading(true);
    try {
      const records = await apiFetch<Array<Record<string, unknown>>>(
        `/chats?project_id=${encodeURIComponent(projectId)}`,
      );
      setChats(
        (records || []).map((r) => ({
          id: String(r.id || ""),
          title: String(r.title || "Conversation"),
          updated_at: String(r.updated_at || r.created_at || ""),
        })),
      );
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to load conversations",
      });
    } finally {
      setChatsLoading(false);
    }
  }, [projectId, addToast]);

  React.useEffect(() => {
    if (activeTab === "conversations") void loadChats();
  }, [activeTab, loadChats]);

  // ── Catalogue Configuration (chargé une seule fois, à la demande) ───────
  React.useEffect(() => {
    if (activeTab !== "configuration" || catalogLoaded) return;
    let cancelled = false;
    Promise.allSettled([
      listProviders(),
      listAgents(),
      listCollections(),
      listSkills(),
      listTools(),
    ]).then(([providersRes, agentsRes, collectionsRes, skillsRes, toolsRes]) => {
      if (cancelled) return;
      if (providersRes.status === "fulfilled") setProviders(providersRes.value);
      if (agentsRes.status === "fulfilled") setAgents(agentsRes.value);
      if (collectionsRes.status === "fulfilled") setCollections(collectionsRes.value);
      if (skillsRes.status === "fulfilled") setSkills(skillsRes.value);
      if (toolsRes.status === "fulfilled") setTools(toolsRes.value);
      setCatalogLoaded(true);
    });
    return () => {
      cancelled = true;
    };
  }, [activeTab, catalogLoaded]);

  /** Patch partiel du projet — la mise à jour Core renvoie la vérité. */
  const patchProject = async (patch: ProjectPatch) => {
    if (!project) return;
    setSaving(true);
    try {
      const updated = await updateProjectInStore(project.id, patch);
      setProject(updated);
      addToast({ type: "success", message: "Project updated" });
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to update project",
      });
      // Resynchronisation avec le Core en cas d'échec (jamais d'état fantôme).
      await loadProject();
    } finally {
      setSaving(false);
    }
  };

  const handleSaveInstructions = async () => {
    if (!project) return;
    if (!name.trim()) {
      addToast({ type: "error", message: "Project name is required" });
      return;
    }
    await patchProject({
      name: name.trim(),
      description: description.trim(),
      instructions: instructions.trim(),
    });
  };

  const handleDelete = async () => {
    if (!project) return;
    try {
      await deleteProjectInStore(project.id);
      addToast({ type: "success", message: `Project "${project.name}" deleted` });
      router.push("/");
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to delete project",
      });
    }
  };

  /**
   * Ouvre la conversation dans le chat : le projet devient le scope actif
   * (résolu par le store Core) puis la conversation est sélectionnée.
   */
  const openChat = async (chatId?: string) => {
    if (!project) return;
    try {
      await setActiveProject(project.id);
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to activate project",
      });
      return;
    }
    if (chatId) setPendingChat(chatId);
    router.push("/");
  };

  const handleNewConversation = async () => {
    if (!project || creatingChat) return;
    setCreatingChat(true);
    try {
      // Création Core (ChatStore) : la conversation naît rattachée au projet.
      const chat = await createChat("Nouvelle conversation", "anonymous", project.id);
      await openChat(chat.id);
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to create conversation",
      });
    } finally {
      setCreatingChat(false);
    }
  };

  /** Toggle d'un id dans une liste du projet (knowledge/skill/tool). */
  const toggleId = (list: string[] | undefined, id: string): string[] => {
    const current = list ?? [];
    return current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (loadError || !project) {
    return (
      <div className="mx-auto max-w-xl p-8 text-center">
        <p className="text-sm text-muted-foreground">{loadError ?? "Project not found"}</p>
        <Link href="/" className="mt-4 inline-block text-sm text-accent hover:underline">
          Back to chat
        </Link>
      </div>
    );
  }

  const provider = providers.find((p) => p.id === project.provider_id);
  const modelOptions = provider?.models ?? [];
  const knowledgeIds = project.knowledge_ids ?? [];
  const skillIds = project.skill_ids ?? [];
  const toolIds = project.tool_ids ?? [];

  return (
    <div className="mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col gap-4 overflow-y-auto p-6">
      {/* En-tête : identité du projet + actions rapides */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Link
            href="/"
            className="mt-0.5 rounded p-1 text-muted-foreground hover:bg-accent"
            aria-label="Retour au chat"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-lg font-semibold">{project.name}</h1>
            {project.description && (
              <p className="text-sm text-muted-foreground">{project.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => void openChat()}>
            Open in chat
          </Button>
          <Button size="sm" onClick={() => void handleNewConversation()} disabled={creatingChat}>
            <MessageSquarePlus className="h-4 w-4" />
            {creatingChat ? "Creating…" : "New conversation"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setConfirmDelete(true)}
            aria-label="Delete project"
          >
            <Trash2 className="h-4 w-4 text-error-600" />
          </Button>
        </div>
      </div>

      {/* Onglets */}
      <div className="flex flex-wrap gap-1 border-b border-line-1/50">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setActiveTab(id)}
            className={
              activeTab === id
                ? "flex items-center gap-1.5 border-b-2 border-accent px-3 py-2 text-sm font-medium text-foreground"
                : "flex items-center gap-1.5 px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>


      {/* ── Instructions ─────────────────────────────────────────────── */}
      {activeTab === "instructions" && (
        <div className="space-y-4 rounded-lg border border-line-1/60 p-4">
          <p className="text-xs text-muted-foreground">
            Les instructions sont injectées en tête du prompt Core pour chaque
            conversation du projet (résolution Chat → Projet). Le nom est unique.
          </p>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="project-name">Name</label>
            <Input
              id="project-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={saving}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="project-description">Description</label>
            <Input
              id="project-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Short description (optional)"
              disabled={saving}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="project-instructions">Instructions</label>
            <Textarea
              id="project-instructions"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Contexte, règles, ton… (injectés dans le prompt de chaque conversation)"
              rows={8}
              disabled={saving}
            />
          </div>
          <div className="flex justify-end">
            <Button size="sm" onClick={() => void handleSaveInstructions()} disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </Button>
          </div>
        </div>
      )}

      {/* ── Fichiers (RAG Core — aucun parseur côté WebUI) ───────────── */}
      {activeTab === "files" && (
        <div className="space-y-4">
          <FileUploadDropzone
            projectId={projectId}
            onUploaded={() => setFilesRefreshKey((k) => k + 1)}
          />
          <div>
            <h2 className="mb-3 text-sm font-medium">Documents indexés</h2>
            <ProjectFilesTable
              projectId={projectId}
              refreshKey={filesRefreshKey}
              onDeleted={() => setFilesRefreshKey((k) => k + 1)}
            />
          </div>
        </div>
      )}

      {/* ── Conversations (ChatStore Core, scope projet) ─────────────── */}
      {activeTab === "conversations" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              Chaque conversation possède son propre historique ; toutes partagent
              le contexte du projet sans fusionner leurs messages.
            </p>
            <Button size="sm" variant="outline" onClick={() => void handleNewConversation()} disabled={creatingChat}>
              <MessageSquarePlus className="h-4 w-4" />
              New
            </Button>
          </div>
          {chatsLoading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : chats.length === 0 ? (
            <p className="rounded-lg border border-line-1/60 p-4 text-sm text-muted-foreground">
              No conversation in this project yet.
            </p>
          ) : (
            <ul className="divide-y divide-line-1/50 rounded-lg border border-line-1/60">
              {chats.map((chat) => (
                <li key={chat.id}>
                  <button
                    type="button"
                    onClick={() => void openChat(chat.id)}
                    className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left text-sm hover:bg-accent"
                  >
                    <span className="truncate">{chat.title}</span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {chat.updated_at ? new Date(chat.updated_at).toLocaleString() : ""}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}


      {/* ── Configuration (défauts d'exécution du projet) ────────────── */}
      {activeTab === "configuration" && (
        <div className="space-y-5 rounded-lg border border-line-1/60 p-4">
          <p className="text-xs text-muted-foreground">
            Ces valeurs sont des défauts : le Core les applique aux conversations
            du projet lorsque la requête ne précise rien (priorité à l&apos;appel
            explicite). La conversation conserve son propre historique.
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="project-provider">Provider</label>
              <select
                id="project-provider"
                className={SELECT_CLASS}
                value={project.provider_id ?? ""}
                disabled={saving}
                onChange={(e) =>
                  void patchProject({ provider_id: e.target.value || null, model: null })
                }
              >
                <option value="">— Default —</option>
                {providers.map((p) => (
                  <option key={p.id} value={p.id}>{p.name || p.id}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="project-model">Model</label>
              <select
                id="project-model"
                className={SELECT_CLASS}
                value={project.model ?? ""}
                disabled={saving || !project.provider_id}
                onChange={(e) => void patchProject({ model: e.target.value || null })}
              >
                <option value="">— Provider default —</option>
                {modelOptions.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="project-agent">Agent</label>
            <select
              id="project-agent"
              className={`${SELECT_CLASS} w-full`}
              value={project.agent_id ?? ""}
              disabled={saving}
              onChange={(e) => void patchProject({ agent_id: e.target.value || null })}
            >
              <option value="">— No agent —</option>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <div className="space-y-2">
              <p className="text-sm font-medium">Knowledge</p>
              <CheckList
                items={collections.map((c) => ({ id: c.id, name: c.name }))}
                selected={knowledgeIds}
                disabled={saving}
                onToggle={(id) => {
                  const next = toggleId(knowledgeIds, id);
                  // knowledge_ids est la portée RAG lue par le pipeline Core ;
                  // collection_ids est conservé en miroir (parité agents).
                  void patchProject({ knowledge_ids: next, collection_ids: next });
                }}
              />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Skills</p>
              <CheckList
                items={skills.map((s) => ({ id: s.id, name: s.name }))}
                selected={skillIds}
                disabled={saving}
                onToggle={(id) => void patchProject({ skill_ids: toggleId(skillIds, id) })}
              />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Tools</p>
              <CheckList
                items={tools.map((t) => ({ id: t.id, name: t.name }))}
                selected={toolIds}
                disabled={saving}
                onToggle={(id) => void patchProject({ tool_ids: toggleId(toolIds, id) })}
              />
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Delete project"
        message={`Supprimer « ${project.name} » ? Les conversations restent conservées (rattachement orphelin).`}
        confirmLabel="Delete"
        destructive
        onConfirm={() => void handleDelete()}
      />
    </div>
  );
}

/** Liste cochable compacte (configuration projet — knowledge/skills/tools). */
function CheckList({
  items,
  selected,
  disabled,
  onToggle,
}: {
  items: Array<{ id: string; name: string }>;
  selected: string[];
  disabled?: boolean;
  onToggle: (id: string) => void;
}) {
  if (items.length === 0) {
    return <p className="text-xs text-muted-foreground">No entries available.</p>;
  }
  return (
    <div className="max-h-56 space-y-0.5 overflow-y-auto rounded-md border border-line-1/60 p-2">
      {items.map((item) => (
        <label
          key={item.id}
          className="flex cursor-pointer items-center gap-2 rounded px-1 py-0.5 text-sm hover:bg-accent"
        >
          <input
            type="checkbox"
            checked={selected.includes(item.id)}
            disabled={disabled}
            onChange={() => onToggle(item.id)}
          />
          <span className="truncate">{item.name}</span>
        </label>
      ))}
    </div>
  );
}

