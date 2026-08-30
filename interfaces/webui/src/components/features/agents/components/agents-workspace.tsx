"use client";

/**
 * ETHAN WebUI — AgentsWorkspace (card-grid refactor)
 * Inspiré de l'UX d'Open WebUI : grille de cartes + recherche + menu contextuel.
 * Toutes les données proviennent du Core via les hooks existants ; aucun système
 * backend n'est réinventé : éditeur/exécution réutilisent les dialogs existants.
 */

import * as React from "react";
import {
  useAgents,
  useUpdateAgent,
  useDeleteAgent,
  useExecuteAgent,
  useCreateAgent,
} from "@/components/features/agents/hooks/use-agents";
import { AgentEditorDialog } from "@/components/features/agents/components/agent-editor-dialog";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { useUIStore } from "@/store/ui.store";
import { useQueryClient } from "@tanstack/react-query";
import {
  Plus, Search, Bot, Play, Pause, Square, Loader2, MoreVertical,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Agent } from "@/types";

const STATUS_MAP: Record<string, { label: string; dot: string }> = {
  running: { label: "Actif", dot: "bg-green-500" },
  paused: { label: "En pause", dot: "bg-amber-500" },
  error: { label: "Erreur", dot: "bg-red-500" },
  idle: { label: "Inactif", dot: "bg-foreground-tertiary/30" },
  stopped: { label: "Arrêté", dot: "bg-foreground-tertiary/40" },
};

export function AgentsWorkspace() {
  const { agents, isLoading, error } = useAgents();
  const updateAgent = useUpdateAgent();
  const deleteAgent = useDeleteAgent();
  const createAgent = useCreateAgent();
  const execute = useExecuteAgent();
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const [search, setSearch] = React.useState("");
  const [editorOpen, setEditorOpen] = React.useState(false);
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [menuAgent, setMenuAgent] = React.useState<Agent | null>(null);
  const [menuPos, setMenuPos] = React.useState<{ x: number; y: number } | null>(null);
  const [execOpen, setExecOpen] = React.useState(false);
  const [execAgent, setExecAgent] = React.useState<Agent | null>(null);
  const [execTask, setExecTask] = React.useState("");
  const [execResult, setExecResult] = React.useState("");
  const [execError, setExecError] = React.useState<string | null>(null);

  const openEditor = (id: string | null) => { setEditingId(id); setEditorOpen(true); };
  const openExecute = (agent: Agent) => {
    setExecAgent(agent); setExecTask(""); setExecResult(""); setExecError(null); setExecOpen(true);
  };

  const handleControl = async (id: string, status: "running" | "paused" | "stopped") => {
    const { error } = await updateAgent.mutate(id, { status });
    if (error) { addToast({ type: "error", message: error }); }
    else {
      const map = { running: "démarré", paused: "mis en pause", stopped: "arrêté" };
      addToast({ type: "success", message: `Agent ${map[status]}` });
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    }
  };

  const handleDelete = async (id: string) => {
    const { error } = await deleteAgent.mutate(id);
    if (error) { addToast({ type: "error", message: error }); }
    else { addToast({ type: "success", message: "Agent supprimé" }); queryClient.invalidateQueries({ queryKey: ["agents"] }); }
  };

  const handleDuplicate = async (agent: Agent) => {
    const { error } = await createAgent.mutate({
      name: `${agent.name} (copie)`,
      description: agent.description ?? undefined,
      capabilities: agent.capabilities,
      model: agent.model ?? undefined,
      provider: agent.provider ?? undefined,
      skill_ids: agent.skill_ids ?? [],
      metadata: { ...(agent.metadata ?? {}) },
    });
    if (error) { addToast({ type: "error", message: error }); }
    else { addToast({ type: "success", message: "Agent dupliqué" }); queryClient.invalidateQueries({ queryKey: ["agents"] }); }
  };

  const handleUseInChat = (agent: Agent) => {
    addToast({ type: "info", message: `Sélectionnez « ${agent.name} » dans le sélecteur Agent du chat.` });
  };

  const handleRunExecute = async () => {
    if (!execAgent || !execTask.trim()) return;
    setExecError(null); setExecResult("");
    const { data, error } = await execute.mutate({ id: execAgent.id, task: execTask.trim() });
    if (error) setExecError(error);
    else if (data) {
      if (data.status === "failed") setExecError(data.error || "Échec de l'exécution");
      else { setExecResult(String((data as any).result ?? "(réponse vide)")); queryClient.invalidateQueries({ queryKey: ["agents"] }); }
    }
  };

  const handleMenu = (e: React.MouseEvent, agent: Agent) => {
    e.stopPropagation();
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setMenuPos({ x: r.right - 8, y: Math.min(r.bottom + 8, window.innerHeight - 220) });
    setMenuAgent(agent);
  };

  React.useEffect(() => {
    if (!menuAgent) return;
    const onDoc = () => setMenuAgent(null);
    document.addEventListener("click", onDoc);
    return () => document.removeEventListener("click", onDoc);
  }, [menuAgent]);

  const filtered = agents.filter((a) => a.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PageHeader
        title="Agents"
        description="Agents ETHAN — personnalités, capacités et automatisations, exécutées par le Core."
        icon={<Bot className="h-5 w-5" />}
        count={agents.length}
        actions={
          <Button size="sm" variant="primary" onClick={() => openEditor(null)}>
            <Plus className="h-4 w-4" />
            <span className="ml-1">Nouvel agent</span>
          </Button>
        }
      />
      <div className="flex items-center justify-between border-b border-line-1 px-4 py-2">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
          <input
            type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher un agent…"
            className="w-full rounded-lg border border-line-1 bg-bg-1 py-1.5 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
          />
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center py-12 text-foreground-tertiary">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="ml-2">Chargement des agents…</span>
          </div>
        )}
        {error && <p className="px-4 py-2 text-sm text-red/80">{error}</p>}

        {!isLoading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10">
              <Bot className="h-6 w-6 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">Aucun agent</h2>
            <p className="mt-2 max-w-sm text-sm text-foreground-tertiary">
              Créez un agent pour configurer ses instructions, son modèle, ses skills et ses outils.
            </p>
            <Button className="mt-4" variant="primary" onClick={() => openEditor(null)}>
              <Plus className="h-4 w-4" />
              <span className="ml-1">Créer un agent</span>
            </Button>
          </div>
        )}

        {!isLoading && filtered.length > 0 && (
          <div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filtered.map((agent) => {
              const st = STATUS_MAP[agent.status] || STATUS_MAP.stopped;
              const caps = agent.capabilities || [];
              const toolsCount = (agent.metadata?.tool_ids as string[] | undefined)?.length || 0;
              const knowledgeCount = (agent.metadata?.knowledge_ids as string[] | undefined)?.length || 0;
              const skillsCount = agent.skill_ids?.length || 0;

              return (
                <div
                  key={agent.id}
                  className="group relative flex flex-col rounded-xl border border-line-1 bg-bg-1/40 p-4 transition-all hover:border-accent/50 hover:shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex cursor-pointer items-center gap-2" onClick={() => openEditor(agent.id)}>
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
                        <Bot className="h-4 w-4 text-accent" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">{agent.name}</p>
                        {agent.description && (
                          <p className="text-xs text-foreground-tertiary line-clamp-2 max-w-[180px]">
                            {agent.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={(e) => handleMenu(e, agent)}
                      className="rounded p-1 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-bg-2"
                      aria-label="Plus d'actions"
                    >
                      <MoreVertical size={14} />
                    </button>
                  </div>

                  <div className="mt-3 flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-xs">
                      <span className={cn("h-2 w-2 shrink-0 rounded-full", st.dot)} />
                      <span className="text-foreground-secondary">{st.label}</span>
                    </div>
                    {(agent.provider || agent.model) && (
                      <p className="text-xs text-foreground-tertiary">
                        {agent.provider && <span className="font-medium">{agent.provider}</span>}
                        {agent.provider && agent.model && <span> · </span>}
                        {agent.model && <span>{agent.model}</span>}
                      </p>
                    )}
                    {caps.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {caps.slice(0, 3).map((c) => (
                          <Badge key={c} variant="dim" size="sm">{c}</Badge>
                        ))}
                        {caps.length > 3 && <Badge variant="dim" size="sm">+{caps.length - 3}</Badge>}
                      </div>
                    )}
                  </div>

                  {(toolsCount > 0 || skillsCount > 0 || knowledgeCount > 0) && (
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-foreground-tertiary">
                      {toolsCount > 0 && <span>🛠 {toolsCount} outils</span>}
                      {skillsCount > 0 && <span>🧠 {skillsCount} skills</span>}
                      {knowledgeCount > 0 && <span>📚 {knowledgeCount} connaissances</span>}
                    </div>
                  )}

                  <div className="mt-2 flex items-center justify-end gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    {agent.status === "running" ? (
                      <Button size="sm" variant="ghost" className="h-6 w-6 p-0"
                        onClick={(e) => { e.stopPropagation(); handleControl(agent.id, "paused"); }} title="Pause">
                        <Pause className="h-3 w-3" />
                      </Button>
                    ) : (
                      <Button size="sm" variant="ghost" className="h-6 w-6 p-0"
                        onClick={(e) => { e.stopPropagation(); handleControl(agent.id, "running"); }} title="Démarrer">
                        <Play className="h-3 w-3" />
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" className="h-6 w-6 p-0"
                      onClick={(e) => { e.stopPropagation(); handleControl(agent.id, "stopped"); }} title="Arrêter">
                      <Square className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {menuAgent && menuPos && (
        <div
          className="fixed z-50 min-w-[180px] rounded-lg border border-line-1 bg-bg-1/95 py-1 shadow-lg backdrop-blur-sm"
          style={{ left: menuPos.x, top: menuPos.y }}
        >
          <button className="w-full px-3 py-1.5 text-left text-sm hover:bg-bg-2"
            onClick={() => { openEditor(menuAgent.id); setMenuAgent(null); }}>Configurer</button>
          <button className="w-full px-3 py-1.5 text-left text-sm hover:bg-bg-2"
            onClick={() => { openExecute(menuAgent); setMenuAgent(null); }}>Exécuter une tâche</button>
          <button className="w-full px-3 py-1.5 text-left text-sm hover:bg-bg-2"
            onClick={() => { handleUseInChat(menuAgent); setMenuAgent(null); }}>Utiliser dans le chat</button>
          <button className="w-full px-3 py-1.5 text-left text-sm hover:bg-bg-2"
            onClick={() => { handleDuplicate(menuAgent); setMenuAgent(null); }}>Dupliquer</button>
          <hr className="my-1 border-line-1" />
          <button className="w-full px-3 py-1.5 text-left text-sm text-red hover:bg-red/10"
            onClick={() => {
              const ok = window.confirm(`Supprimer l'agent « ${menuAgent.name} » ? Cette action est irréversible.`);
              if (ok) handleDelete(menuAgent.id);
              setMenuAgent(null);
            }}>Supprimer</button>
        </div>
      )}

      <AgentEditorDialog open={editorOpen} onOpenChange={setEditorOpen} agentId={editingId} />

      <Dialog
        open={execOpen} onClose={() => setExecOpen(false)}
        title={`Exécuter — ${execAgent?.name ?? "Agent"}`} size="lg"
      >
        <div className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Tâche</label>
            <Textarea
              value={execTask} onChange={(e) => setExecTask(e.target.value)}
              placeholder="Décrivez la tâche à confier à l'agent…" rows={3}
            />
          </div>
          {execError && (
            <div className="rounded-lg border border-red-soft bg-red-soft px-3 py-2 text-sm text-red">{execError}</div>
          )}
          {execute.isLoading && (
            <div className="flex items-center gap-2 text-sm text-foreground-tertiary">
              <Loader2 className="h-4 w-4 animate-spin" />
              Exécution via le LLM Core… (quelques secondes)
            </div>
          )}
          {execResult && (
            <div>
              <label className="mb-1 block text-sm font-medium">Résultat</label>
              <pre className="whitespace-pre-wrap rounded-lg border border-line-1 bg-bg-1 p-3 text-sm text-foreground-secondary">
                {execResult}
              </pre>
            </div>
          )}
          <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
            <Button variant="secondary" onClick={() => setExecOpen(false)}>Fermer</Button>
            <Button onClick={handleRunExecute} disabled={!execTask.trim() || execute.isLoading}>
              {execute.isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              Exécuter
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
