"use client";

import * as React from "react";
import { useAgents, useUpdateAgent, useDeleteAgent, useExecuteAgent } from "@/components/features/agents/hooks/use-agents";
import { AgentEditorDialog } from "@/components/features/agents/components/agent-editor-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog } from "@/components/ui/dialog";
import { useUIStore } from "@/store/ui.store";
import { useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Search,
  Trash2,
  Bot,
  Play,
  Pause,
  Square,
  Settings2,
  MessageSquare,
  MoreVertical,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Agent } from "@/types";

const statusMap: Record<string, { label: string; dot: string }> = {
  running: { label: "Actif", dot: "bg-green-500" },
  paused: { label: "En pause", dot: "bg-amber-500" },
  error: { label: "Erreur", dot: "bg-red-500" },
  idle: { label: "Inactif", dot: "bg-muted-foreground/30" },
  stopped: { label: "Arrêté", dot: "bg-muted-foreground/40" },
};

export function AgentsWorkspace() {
  const { agents, isLoading, error, refetch } = useAgents();
  const updateAgent = useUpdateAgent();
  const deleteAgent = useDeleteAgent();
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const [search, setSearch] = React.useState("");
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [editorOpen, setEditorOpen] = React.useState(false);
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [actionLoading, setActionLoading] = React.useState<string | null>(null);
  const execute = useExecuteAgent();
  const [executeOpen, setExecuteOpen] = React.useState(false);
  const [executeTask, setExecuteTask] = React.useState("");
  const [executionResult, setExecutionResult] = React.useState<string>("");
  const [executeError, setExecuteError] = React.useState<string | null>(null);

  const handleExecute = async () => {
    if (!selectedId || !executeTask.trim()) return;
    setExecuteError(null);
    setExecutionResult("");
    const result = await execute.mutate({ id: selectedId, task: executeTask.trim() });
    if (result.error) {
      setExecuteError(result.error);
    } else if (result.data) {
      if (result.data.status === "failed") {
        setExecuteError(result.data.error || "Échec de l'exécution");
        setExecutionResult("");
      } else {
        setExecutionResult(String(result.data.result ?? "(réponse vide)"));
        queryClient.invalidateQueries({ queryKey: ["agents"] });
      }
    }
  };

  const filteredAgents = agents.filter((a) =>
    a.name.toLowerCase().includes(search.toLowerCase()),
  );
  const selectedAgent = agents.find((a) => a.id === selectedId) || null;

  const handleControl = async (id: string, status: "running" | "paused" | "stopped") => {
    setActionLoading(id);
    const result = await updateAgent.mutate(id, { status });
    if (result.error) {
      addToast({ type: "error", message: result.error });
    } else {
      addToast({ type: "success", message: `Agent ${status === "running" ? "démarré" : status === "paused" ? "mis en pause" : "arrêté"}` });
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    }
    setActionLoading(null);
  };

  const handleDelete = async (id: string) => {
    const result = await deleteAgent.mutate(id);
    if (result.error) {
      addToast({ type: "error", message: result.error });
    } else {
      addToast({ type: "success", message: "Agent supprimé" });
      if (selectedId === id) setSelectedId(null);
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    }
  };

  const handleEdit = (id: string | null) => {
    setEditingId(id);
    setEditorOpen(true);
  };

  const handleUseInChat = () => {
    if (selectedId) {
      addToast({ type: "info", message: "Sélectionnez l'agent dans le menu du chat (bouton + → Agent)" });
    }
  };

  return (
    <div className="flex h-full min-h-0">
      {/* Left panel: agents list */}
      <div className="flex w-72 shrink-0 flex-col border-r border-line-1 bg-bg-1/40">
        <div className="flex items-center justify-between border-b border-line-1 px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground">Agents</h2>
          <Button size="sm" variant="primary" onClick={() => handleEdit(null)}>
            <Plus className="h-3.5 w-3.5" />
            <span className="ml-1">Nouveau</span>
          </Button>
        </div>

        <div className="p-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher un agent..."
              className="w-full rounded-lg border border-line-1 bg-bg-1 py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {isLoading && (
            <div className="flex items-center justify-center py-8 text-foreground-tertiary">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          )}
          {error && <p className="px-3 py-2 text-xs text-red/80">{error}</p>}
          {filteredAgents.map((agent) => {
            const status = statusMap[agent.status] || statusMap.stopped;
            return (
              <div
                key={agent.id}
                onClick={() => setSelectedId(agent.id)}
                className={cn(
                  "flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors",
                  agent.id === selectedId ? "bg-bg-3 text-foreground" : "text-foreground-secondary hover:bg-bg-3/60"
                )}
              >
                <span className={cn("h-2 w-2 shrink-0 rounded-full", status.dot)} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{agent.name}</p>
                  <p className="truncate text-xs text-foreground-tertiary">
                    {agent.capabilities?.slice(0, 2).join(", ") || "Aucune capacité"}
                  </p>
                </div>
              </div>
            );
          })}
          {filteredAgents.length === 0 && !isLoading && (
            <p className="px-3 py-6 text-center text-xs text-foreground-tertiary">Aucun agent</p>
          )}
        </div>
      </div>

      {/* Right panel: agent details */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        {!selectedAgent ? (
          <div className="flex h-full flex-col items-center justify-center text-center px-4">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10">
              <Bot className="h-6 w-6 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">Sélectionnez un agent</h2>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              Créez un agent ou sélectionnez-en un pour configurer son modèle, ses skills, ses outils et ses instructions.
            </p>
            <Button className="mt-4" variant="primary" onClick={() => handleEdit(null)}>
              <Plus className="h-4 w-4" />
              <span className="ml-1">Créer un agent</span>
            </Button>
          </div>
        ) : (
          <div className="p-6">
            {/* Header */}
            <div className="mb-6 flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/10">
                  <Bot className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-foreground">{selectedAgent.name}</h1>
                  {selectedAgent.description && (
                    <p className="mt-0.5 text-sm text-muted-foreground">{selectedAgent.description}</p>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="default"
                  onClick={() => {
                    setExecuteTask("");
                    setExecutionResult("");
                    setExecuteError(null);
                    setExecuteOpen(true);
                  }}
                  disabled={execute.isLoading}
                  title="Exécuter une tâche avec cet agent"
                >
                  {execute.isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                  <span className="ml-1">Exécuter</span>
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleUseInChat()}
                  title="Utiliser cet agent dans le chat"
                >
                  <MessageSquare className="h-3.5 w-3.5" />
                  <span className="ml-1">Chat</span>
                </Button>
                <Button size="sm" variant="secondary" onClick={() => handleEdit(selectedAgent.id)}>
                  <Settings2 className="h-3.5 w-3.5" />
                  <span className="ml-1">Configurer</span>
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red/80 hover:text-red"
                  onClick={() => handleDelete(selectedAgent.id)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>

            {/* Status + controls */}
            <div className="mb-6 flex items-center gap-3 rounded-lg border border-line-1 bg-bg-1/50 p-3">
              <span className={cn("h-2.5 w-2.5 rounded-full", (statusMap[selectedAgent.status] || statusMap.stopped).dot)} />
              <span className="text-sm font-medium text-foreground-secondary">
                {(statusMap[selectedAgent.status] || statusMap.stopped).label}
              </span>
              <span className="flex-1" />
              {actionLoading === selectedAgent.id ? (
                <Loader2 className="h-4 w-4 animate-spin text-foreground-tertiary" />
              ) : (
                <>
                  {selectedAgent.status !== "running" && (
                    <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => handleControl(selectedAgent.id, "running")} title="Démarrer">
                      <Play className="h-3.5 w-3.5" />
                    </Button>
                  )}
                  {selectedAgent.status === "running" && (
                    <>
                      <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => handleControl(selectedAgent.id, "paused")} title="Pause">
                        <Pause className="h-3.5 w-3.5" />
                      </Button>
                      <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-red/80" onClick={() => handleControl(selectedAgent.id, "stopped")} title="Arrêter">
                        <Square className="h-3.5 w-3.5" />
                      </Button>
                    </>
                  )}
                </>
              )}
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              {/* Model & Provider */}
              <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
                <h3 className="mb-3 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">
                  Modèle
                </h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-foreground-tertiary">Modèle</dt>
                    <dd className="font-mono text-foreground-secondary">{selectedAgent.model || "Par défaut"}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-foreground-tertiary">Provider</dt>
                    <dd className="text-foreground-secondary">{selectedAgent.provider || "Par défaut"}</dd>
                  </div>
                </dl>
              </div>

              {/* Capabilities */}
              <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
                <h3 className="mb-3 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">
                  Capacités
                </h3>
                {selectedAgent.capabilities?.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {selectedAgent.capabilities.map((cap) => (
                      <span key={cap} className="rounded-full bg-accent/10 px-2.5 py-0.5 text-xs text-accent">
                        {cap}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-foreground-tertiary">Aucune capacité configurée</p>
                )}
              </div>

              {/* Skills */}
              <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
                <h3 className="mb-3 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">
                  Skills ({(selectedAgent.skill_ids || []).length})
                </h3>
                {(selectedAgent.skill_ids || []).length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {(selectedAgent.skill_ids || []).map((id) => (
                      <span key={id} className="rounded-full bg-bg-2 px-2.5 py-0.5 text-xs text-foreground-secondary">
                        {id.slice(0, 24)}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-foreground-tertiary">Aucun skill sélectionné</p>
                )}
              </div>

              {/* Memory / Meta */}
              <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
                <h3 className="mb-3 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">
                  Mémoire
                </h3>
                <p className="text-sm text-foreground-secondary">
                  {selectedAgent.memory_scope ? `Scope: ${selectedAgent.memory_scope}` : "Par défaut"}
                </p>
                {selectedAgent.metadata && Object.keys(selectedAgent.metadata).length > 0 && (
                  <div className="mt-3 space-y-1">
                    {Object.entries(selectedAgent.metadata).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-xs">
                        <span className="text-foreground-tertiary">{k}</span>
                        <span className="text-foreground-secondary">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Footer meta */}
            <div className="mt-6 border-t border-line-1 pt-3 text-xs text-foreground-tertiary">
              Créé le {new Date(selectedAgent.created_at).toLocaleDateString("fr-FR")} · Dernière mise à jour le {new Date(selectedAgent.updated_at).toLocaleDateString("fr-FR")}
            </div>
          </div>
        )}
      </div>

      {/* Editor dialog */}
      <AgentEditorDialog
        open={editorOpen}
        onOpenChange={setEditorOpen}
        agentId={editingId}
      />

      {/* Execute task dialog */}
      <Dialog open={executeOpen} onClose={() => setExecuteOpen(false)} title={`Exécuter — ${selectedAgent?.name ?? "Agent"}`} size="lg">
        <div className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Tâche</label>
            <Textarea
              value={executeTask}
              onChange={(e) => setExecuteTask(e.target.value)}
              placeholder="Décrivez la tâche à confier à l'agent…"
              rows={3}
              className="w-full"
            />
          </div>

          {executeError && (
            <div className="rounded-lg border border-red-soft bg-red-soft px-3 py-2 text-sm text-red">
              {executeError}
            </div>
          )}

          {execute.isLoading && (
            <div className="flex items-center gap-2 text-sm text-foreground-tertiary">
              <Loader2 className="h-4 w-4 animate-spin" />
              Exécution via le LLM Core… (peut prendre plusieurs secondes)
            </div>
          )}

          {executionResult && (
            <div>
              <label className="mb-1 block text-sm font-medium">Résultat</label>
              <pre className="whitespace-pre-wrap rounded-lg border border-line-1 bg-bg-1 p-3 text-sm text-foreground-secondary">
                {executionResult}
              </pre>
            </div>
          )}

          <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
            <Button variant="secondary" onClick={() => setExecuteOpen(false)}>Fermer</Button>
            <Button
              onClick={handleExecute}
              disabled={!executeTask.trim() || execute.isLoading}
            >
              {execute.isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              Exécuter
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}