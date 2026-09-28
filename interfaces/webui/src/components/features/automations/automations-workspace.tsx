"use client";

/**
 * AutomationsWorkspace — surface des automatisations stockées par ETHAN Core
 * (AutomationManager, core/scheduler/automations.py ; routes /v1/automations).
 *
 * L'interface liste, crée, active/désactive, déclenche et supprime des règles.
 * « Déclencher » est un vrai POST Core : il met à jour last_triggered_at /
 * trigger_count et publie `automation.triggered` sur le bus — l'exécution des
 * actions reste du ressort du Runtime (aucun moteur parallèle dans la WebUI).
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  listAutomations,
  createAutomation,
  updateAutomation,
  deleteAutomation,
  triggerAutomation,
  type Automation,
} from "@/lib/api/automations";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { AlertCircle, Loader2, Play, Plus, Power, PowerOff, Trash2, Workflow } from "lucide-react";

type EnabledFilter = "all" | "enabled" | "disabled";

const FILTERS: { id: EnabledFilter; label: string }[] = [
  { id: "all", label: "Toutes" },
  { id: "enabled", label: "Actives" },
  { id: "disabled", label: "Inactives" },
];

export function AutomationsWorkspace() {
  const addToast = useUIStore((s) => s.addToast);
  const [filter, setFilter] = React.useState<EnabledFilter>("all");
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [confirmRule, setConfirmRule] = React.useState<Automation | null>(null);
  const [busyId, setBusyId] = React.useState<string | null>(null);

  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [triggerJson, setTriggerJson] = React.useState('{\n  "type": "manual"\n}');
  const [actionsJson, setActionsJson] = React.useState("[]");
  const [formError, setFormError] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);

  // Filtre délégué au Core (`?enabled=`) — aucun filtrage simulé en local.
  const enabledParam = filter === "all" ? undefined : filter === "enabled";
  const {
    data: rules = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["automations", filter],
    queryFn: () => listAutomations(enabledParam),
    retry: false,
  });

  const resetForm = () => {
    setName("");
    setDescription("");
    setTriggerJson('{\n  "type": "manual"\n}');
    setActionsJson("[]");
    setFormError(null);
  };

  const handleCreate = async () => {
    let trigger: Record<string, unknown>;
    let actions: Array<Record<string, unknown>>;
    try {
      trigger = JSON.parse(triggerJson) as Record<string, unknown>;
      actions = JSON.parse(actionsJson) as Array<Record<string, unknown>>;
    } catch {
      setFormError("Trigger et actions doivent être du JSON valide.");
      return;
    }
    if (!Array.isArray(actions)) {
      setFormError("« actions » doit être une liste JSON.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      await createAutomation({ name, description, trigger, actions });
      addToast({ type: "success", message: `Automation « ${name} » créée` });
      setDialogOpen(false);
      resetForm();
      await refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Création refusée par le Core");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (rule: Automation) => {
    setBusyId(rule.id);
    try {
      await updateAutomation(rule.id, { enabled: !rule.enabled });
      addToast({
        type: "success",
        message: rule.enabled ? "Automation désactivée" : "Automation activée",
      });
      await refetch();
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Échec de la mise à jour",
      });
    } finally {
      setBusyId(null);
    }
  };

  const handleTrigger = async (rule: Automation) => {
    setBusyId(rule.id);
    try {
      await triggerAutomation(rule.id);
      addToast({ type: "success", message: `« ${rule.name} » déclenchée (événement publié)` });
      await refetch();
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Déclenchement refusé",
      });
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async () => {
    if (!confirmRule) return;
    try {
      await deleteAutomation(confirmRule.id);
      addToast({ type: "success", message: `« ${confirmRule.name} » supprimée` });
      await refetch();
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Suppression refusée",
      });
    } finally {
      setConfirmRule(null);
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div
        className="flex items-center justify-between gap-3 border-b border-line-1 px-4 py-3"
        style={{ background: "var(--panel)" }}
      >
        <div className="flex items-center gap-2">
          <Workflow className="h-4 w-4 text-muted-foreground" />
          <div>
            <h1 className="text-sm font-semibold text-foreground">Automations</h1>
            <p className="text-xs text-muted-foreground">
              Règles persistées par ETHAN Core — le déclenchement publie un événement sur le bus.
            </p>
          </div>
        </div>
        <Button
          size="sm"
          onClick={() => {
            resetForm();
            setDialogOpen(true);
          }}
        >
          <Plus className="h-4 w-4" /> Nouvelle automation
        </Button>
      </div>

      <div className="flex items-center gap-2 border-b border-line-1 px-4 py-2">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`rounded-md px-3 py-1 text-xs transition-colors ${
              filter === f.id
                ? "bg-[var(--accent)]/10 text-foreground"
                : "text-foreground-secondary hover:bg-[var(--panel-hover)]"
            }`}
          >
            {f.label}
          </button>
        ))}
        <span className="ml-auto text-xs text-muted-foreground">
          {rules.length} {rules.length > 1 ? "règles" : "règle"}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Chargement des automations…
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-soft bg-red-soft p-4 text-sm text-red">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Impossible de charger les automations
            </div>
            <p className="mt-1 text-xs">
              {error instanceof Error ? error.message : "Core indisponible"}
            </p>
            <Button size="sm" variant="outline" className="mt-3" onClick={() => refetch()}>
              Réessayer
            </Button>
          </div>
        )}

        {!isLoading && !error && rules.length === 0 && (
          <div className="rounded-lg border border-line-1 p-6 text-center">
            <p className="text-sm font-medium text-foreground">Aucune automation</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Les règles créées ici sont stockées par ETHAN Core (AutomationManager) ; elles
              restent disponibles pour le Runtime, la CLI et les autres interfaces.
            </p>
          </div>
        )}

        <div className="space-y-2">
          {rules.map((rule) => (
            <div key={rule.id} className="flex items-start gap-3 rounded-lg border border-line-1 p-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h2 className="truncate text-sm font-medium text-foreground">{rule.name}</h2>
                  <Badge variant={rule.enabled ? "success" : "secondary"}>
                    {rule.enabled ? "Active" : "Inactive"}
                  </Badge>
                </div>
                {rule.description && (
                  <p className="mt-1 text-xs text-muted-foreground">{rule.description}</p>
                )}
                <p className="mt-1 text-xs text-muted-foreground">
                  {rule.trigger_count} déclenchement{rule.trigger_count > 1 ? "s" : ""}
                  {rule.last_triggered_at
                    ? ` · dernier : ${new Date(rule.last_triggered_at).toLocaleString()}`
                    : " · jamais déclenchée"}
                  {` · ${rule.actions.length} action${rule.actions.length > 1 ? "s" : ""}`}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={!rule.enabled || busyId === rule.id}
                  title={rule.enabled ? "Déclencher maintenant" : "Automation inactive"}
                  onClick={() => handleTrigger(rule)}
                >
                  <Play className="h-4 w-4" /> Déclencher
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={busyId === rule.id}
                  onClick={() => handleToggle(rule)}
                >
                  {rule.enabled ? <PowerOff className="h-4 w-4" /> : <Power className="h-4 w-4" />}
                  {rule.enabled ? "Désactiver" : "Activer"}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setConfirmRule(rule)}>
                  <Trash2 className="h-4 w-4" /> Supprimer
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title="Nouvelle automation"
        size="md"
      >
        <div className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Nom</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="ex: résumé quotidien"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Description</label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Trigger (JSON)</label>
            <Textarea
              value={triggerJson}
              onChange={(e) => setTriggerJson(e.target.value)}
              rows={3}
              className="font-mono text-xs"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Actions (JSON)</label>
            <Textarea
              value={actionsJson}
              onChange={(e) => setActionsJson(e.target.value)}
              rows={4}
              className="font-mono text-xs"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Stockées telles quelles par le Core ; leur exécution appartient au Runtime.
            </p>
          </div>
          {formError && <p className="text-sm text-red">{formError}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setDialogOpen(false)}>
              Annuler
            </Button>
            <Button onClick={handleCreate} disabled={saving || !name.trim()}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Créer
            </Button>
          </div>
        </div>
      </Dialog>

      <ConfirmDialog
        open={confirmRule !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmRule(null);
        }}
        title="Supprimer cette automation ?"
        message={confirmRule ? `« ${confirmRule.name} » sera supprimée du Core.` : undefined}
        confirmLabel="Supprimer"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  );
}
