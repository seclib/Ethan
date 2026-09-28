"use client";

/**
 * ETHAN WebUI — dialogs du gestionnaire de capacités.
 *
 * Toutes les opérations délèguent à ETHAN Core (/v1/components) :
 * le plan affiché, la progression et les résultats de test proviennent du
 * Core — aucune progression ni validation n'est inventée côté frontend.
 */

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, Loader2, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useUIStore } from "@/store/ui.store";
import {
  cancelOperation,
  configureComponent,
  getInstallPlan,
  getOperation,
  getUninstallPlan,
  installComponent,
  testComponent,
  uninstallComponent,
  type ComponentStatus,
  type HealthTestResult,
  type OperationStatus,
} from "@/lib/api/components";

/* ── Progression réelle (polling du suivi d'opérations du Core) ────────── */

export function OperationProgress({
  operationId,
  label,
  onFinished,
}: {
  operationId: string;
  label: string;
  onFinished: (ok: boolean, error?: string | null) => void;
}) {
  const addToast = useUIStore((s) => s.addToast);
  const notifiedRef = React.useRef(false);

  // Polling du Core : la progression affichée EST celle du Core.
  const { data: op } = useQuery({
    queryKey: ["component-operation", operationId],
    queryFn: () => getOperation(operationId),
    refetchInterval: (query) => (query.state.data?.done ? false : 1000),
  });

  React.useEffect(() => {
    if (op?.done && !notifiedRef.current) {
      notifiedRef.current = true;
      const ok = !op.error;
      if (ok) {
        addToast({ type: "success", message: `${label} terminé` });
      } else {
        addToast({ type: "error", message: `${label} échoué : ${op.error}` });
      }
      onFinished(ok, op.error);
    }
  }, [op, label, addToast, onFinished]);

  const cancelMutation = useMutation({
    mutationFn: () => cancelOperation(operationId),
    onSuccess: () =>
      addToast({ type: "info", message: "Annulation demandée au Core…" }),
  });

  if (!op) {
    return (
      <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Lecture de la progression…
      </div>
    );
  }

  return (
    <div className="space-y-3 py-2">
      <Progress value={Math.min(op.progress, 100)} max={100} />
      <ul className="space-y-1 text-xs text-muted-foreground" data-testid="operation-steps">
        {op.steps_done.map(([step, ok, detail], i) => (
          <li key={i} className="flex items-start gap-2">
            {ok ? (
              <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-green-500" />
            ) : (
              <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-500" />
            )}
            <span>
              {step}
              {detail ? ` — ${detail}` : ""}
            </span>
          </li>
        ))}
      </ul>
      {!op.done && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => cancelMutation.mutate()}
          disabled={cancelMutation.isPending}
        >
          Annuler
        </Button>
      )}
    </div>
  );
}

/* ── Dialog d'installation (plan Core → confirmation → progression) ────── */

export function InstallDialog({
  component,
  open,
  onClose,
  onCompleted,
}: {
  component: ComponentStatus;
  open: boolean;
  onClose: () => void;
  onCompleted: () => void;
}) {
  const [operationId, setOperationId] = React.useState<string | null>(null);

  const planQuery = useQuery({
    queryKey: ["component-install-plan", component.id],
    queryFn: () => getInstallPlan(component.id),
    enabled: open && !operationId,
  });

  const installMutation = useMutation({
    mutationFn: () => installComponent(component.id),
    onSuccess: (result) => setOperationId(result.operation_id),
  });

  const handleFinished = React.useCallback(
    (ok: boolean) => {
      if (ok) {
        setOperationId(null);
        onCompleted();
        onClose();
      }
    },
    [onCompleted, onClose],
  );

  const plan = planQuery.data;
  return (
    <Dialog
      open={open}
      onClose={operationId ? undefined : onClose}
      title={`Installer ${component.name}`}
      size="lg"
    >
      {operationId ? (
        <div>
          <p className="text-sm text-muted-foreground">
            Installation en cours — progression fournie par ETHAN Core.
          </p>
          <OperationProgress
            operationId={operationId}
            label={`Installation de ${component.name}`}
            onFinished={handleFinished}
          />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-sm">
            <p className="text-muted-foreground">{component.description}</p>
            <p className="mt-1 text-xs text-foreground-tertiary">
              Version {component.version} · backend {component.backend}
            </p>
          </div>

          {component.dependencies.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground-tertiary">
                Dépendances
              </h4>
              <ul className="mt-1 space-y-1 text-sm">
                {component.dependencies.map((d) => (
                  <li key={d.id}>
                    <span className="font-medium">{d.id}</span>
                    <span className="text-muted-foreground"> ({d.kind})</span>
                    {d.description ? (
                      <span className="block text-xs text-muted-foreground">{d.description}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground-tertiary">
              Opérations prévues (fournies par le Core)
            </h4>
            {planQuery.isLoading ? (
              <p className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Lecture du plan…
              </p>
            ) : planQuery.isError ? (
              <p className="mt-1 text-sm text-red-500">Plan indisponible : {(planQuery.error as Error).message}</p>
            ) : (
              <ol className="mt-1 list-inside list-decimal space-y-1 text-sm">
                {plan?.steps.map((s, i) => (
                  <li key={i} className={s.destructive ? "text-red-500" : undefined}>
                    {s.description}
                    {s.destructive ? " ⚠" : ""}
                  </li>
                ))}
              </ol>
            )}
          </div>

          {component.data_resources.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground-tertiary">
                Données qui seront créées
              </h4>
              <ul className="mt-1 space-y-1 text-sm text-muted-foreground">
                {component.data_resources.map((r, i) => (
                  <li key={i}>
                    <span className="font-medium text-foreground">{r.name}</span> ({r.kind})
                    {r.description ? ` — ${r.description}` : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>
              Annuler
            </Button>
            <Button
              onClick={() => installMutation.mutate()}
              disabled={installMutation.isPending || planQuery.isError}
            >
              {installMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Installer"
              )}
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}

/* ── Dialog de désinstallation (choix des données + double confirmation) ─ */

export function UninstallDialog({
  component,
  open,
  onClose,
  onCompleted,
}: {
  component: ComponentStatus;
  open: boolean;
  onClose: () => void;
  onCompleted: () => void;
}) {
  const [deleteData, setDeleteData] = React.useState(false);
  const [confirmDelete, setConfirmDelete] = React.useState(false);
  const [operationId, setOperationId] = React.useState<string | null>(null);
  const addToast = useUIStore((s) => s.addToast);

  // Le plan est recalculé selon le choix keep/delete (fourni par le Core).
  const planQuery = useQuery({
    queryKey: ["component-uninstall-plan", component.id, deleteData],
    queryFn: () => getUninstallPlan(component.id, deleteData),
    enabled: open && !operationId,
  });

  const uninstallMutation = useMutation({
    mutationFn: () => uninstallComponent(component.id, deleteData),
    onSuccess: (result) => setOperationId(result.operation_id),
    onError: (err) =>
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Échec de la désinstallation",
      }),
  });

  React.useEffect(() => {
    if (!open) {
      setDeleteData(false);
      setConfirmDelete(false);
      setOperationId(null);
    }
  }, [open]);

  const handleFinished = React.useCallback(
    (ok: boolean) => {
      if (ok) {
        setOperationId(null);
        onCompleted();
        onClose();
      }
    },
    [onCompleted, onClose],
  );

  const destructivePlan = planQuery.data?.steps.some((s) => s.destructive) ?? false;

  return (
    <>
      <Dialog
        open={open}
        onClose={operationId ? undefined : onClose}
        title={`Désinstaller ${component.name}`}
        size="lg"
      >
        {operationId ? (
          <OperationProgress
            operationId={operationId}
            label={`Désinstallation de ${component.name}`}
            onFinished={handleFinished}
          />
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Cette action supprime le service {component.name}. Le plan ci-dessous est
              fourni par ETHAN Core avant toute exécution.
            </p>

            {component.data_resources.length > 0 && (
              <div className="rounded-lg border border-line-2 p-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground-tertiary">
                  Que faire de ses données ?
                </h4>
                <ul className="mt-1 mb-2 space-y-0.5 text-xs text-muted-foreground">
                  {component.data_resources.map((r, i) => (
                    <li key={i}>
                      {r.name} ({r.kind}){r.description ? ` — ${r.description}` : ""}
                    </li>
                  ))}
                </ul>
                <div className="space-y-2" role="radiogroup" aria-label="Destination des données">
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="radio"
                      name={`data-${component.id}`}
                      checked={!deleteData}
                      onChange={() => setDeleteData(false)}
                    />
                    Conserver les données (réinstallable plus tard)
                  </label>
                  <label className="flex items-center gap-2 text-sm text-red-500">
                    <input
                      type="radio"
                      name={`data-${component.id}`}
                      checked={deleteData}
                      onChange={() => setDeleteData(true)}
                    />
                    Supprimer définitivement les données
                  </label>
                </div>
              </div>
            )}

            {planQuery.isError ? (
              <p className="text-sm text-red-500">Plan indisponible : {(planQuery.error as Error).message}</p>
            ) : (
              <ol className="list-inside list-decimal space-y-1 text-sm">
                {planQuery.data?.steps.map((s, i) => (
                  <li key={i} className={s.destructive ? "text-red-500" : undefined}>
                    {s.description}
                    {s.destructive ? " ⚠" : ""}
                  </li>
                ))}
              </ol>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={onClose}>
                Annuler
              </Button>
              <Button
                variant="destructive"
                onClick={() => (deleteData ? setConfirmDelete(true) : uninstallMutation.mutate())}
                disabled={uninstallMutation.isPending || planQuery.isError}
              >
                {uninstallMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Désinstaller"
                )}
              </Button>
            </div>
          </div>
        )}
      </Dialog>

      {/* Double confirmation : requise par le Core (confirm_delete_data). */}
      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title={`Supprimer définitivement les données de ${component.name} ?`}
        message={
          "Cette action est IRRÉVERSIBLE : " +
          (component.data_resources.map((r) => r.name).join(", ") || "les données") +
          " seront supprimés."
        }
        confirmLabel="Supprimer définitivement"
        destructive
        onConfirm={() => uninstallMutation.mutate()}
      />
      {destructivePlan ? null : null}
    </>
  );
}

/* ── Dialog de configuration (Guided / JSON + test de santé) ───────────── */

function exampleFromSchema(schema: ComponentStatus["config_schema"]): string {
  const example: Record<string, unknown> = {};
  for (const f of schema) {
    if (f.default !== null && f.default !== undefined) {
      example[f.name] = f.default;
    } else if (f.type === "int" || f.type === "port") {
      example[f.name] = f.min_value ?? 0;
    } else if (f.type === "bool") {
      example[f.name] = false;
    } else {
      example[f.name] = "";
    }
  }
  return JSON.stringify(example, null, 2);
}

export function ConfigureDialog({
  component,
  open,
  onClose,
}: {
  component: ComponentStatus;
  open: boolean;
  onClose: () => void;
}) {
  const addToast = useUIStore((s) => s.addToast);
  const queryClient = useQueryClient();
  const [mode, setMode] = React.useState<"guided" | "json">("guided");
  const [values, setValues] = React.useState<Record<string, unknown>>({});
  const [jsonText, setJsonText] = React.useState("");
  const [jsonError, setJsonError] = React.useState<string | null>(null);
  const [testResult, setTestResult] = React.useState<HealthTestResult | null>(null);

  React.useEffect(() => {
    if (open) {
      setMode("guided");
      setTestResult(null);
      setJsonError(null);
      const defaults: Record<string, unknown> = {};
      for (const f of component.config_schema) {
        defaults[f.name] = f.default ?? null;
      }
      setValues(defaults);
      setJsonText(exampleFromSchema(component.config_schema));
    }
  }, [open, component]);

  const parseCurrent = (): Record<string, unknown> | null => {
    if (mode === "guided") return values;
    try {
      return JSON.parse(jsonText) as Record<string, unknown>;
    } catch (err) {
      setJsonError((err as SyntaxError).message);
      return null;
    }
  };

  const configureMutation = useMutation({
    mutationFn: (config: Record<string, unknown>) => configureComponent(component.id, config),
    onSuccess: (result) => {
      addToast({
        type: "success",
        message: `Configuration enregistrée (${result.config_keys.join(", ") || "vide"})`,
      });
      queryClient.invalidateQueries({ queryKey: ["components"] });
      onClose();
    },
    onError: (err) =>
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Configuration refusée par le Core",
      }),
  });

  const testMutation = useMutation({
    mutationFn: () => testComponent(component.id),
    onSuccess: (result) => setTestResult(result),
  });

  const handleSave = () => {
    setJsonError(null);
    const config = parseCurrent();
    if (config) configureMutation.mutate(config);
  };

  const handleFormat = () => {
    try {
      setJsonText(JSON.stringify(JSON.parse(jsonText), null, 2));
      setJsonError(null);
    } catch (err) {
      setJsonError((err as SyntaxError).message);
    }
  };

  const setField = (name: string, value: unknown) =>
    setValues((v) => ({ ...v, [name]: value }));

  return (
    <Dialog open={open} onClose={onClose} title={`Configurer ${component.name}`} size="lg">
      <div className="space-y-4">
        {/* Modes Guided / JSON — section 7 de la spec */}
        <div className="flex items-center gap-1 rounded-lg border border-line-2 p-1 text-sm">
          {(["guided", "json"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`flex-1 rounded px-3 py-1.5 ${
                mode === m ? "bg-accent-600 text-white" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {m === "guided" ? "Guidé" : "JSON"}
            </button>
          ))}
        </div>
        {mode === "json" && (
          <p className="text-xs text-muted-foreground">
            Mode avancé : la validation et les erreurs sont appliquées par le schéma réel du Core.
          </p>
        )}

        {mode === "guided" ? (
          <div className="space-y-3">
            {component.config_schema.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Ce composant ne déclare aucun champ de configuration.
              </p>
            )}
            {component.config_schema.map((f) => (
              <div key={f.name}>
                <label
                  htmlFor={`cfg-${component.id}-${f.name}`}
                  className="text-sm font-medium"
                >
                  {f.name}
                  {f.required && <span className="text-red-500"> *</span>}
                </label>
                <p className="text-xs text-muted-foreground">{f.description}</p>
                {f.choices && f.choices.length > 0 ? (
                  <select
                    id={`cfg-${component.id}-${f.name}`}
                    className="mt-1 h-10 w-full rounded-lg border border-line-2 bg-background px-3 text-sm"
                    value={String(values[f.name] ?? "")}
                    onChange={(e) => setField(f.name, e.target.value)}
                  >
                    {f.choices.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                ) : (
                  <Input
                    id={`cfg-${component.id}-${f.name}`}
                    className="mt-1"
                    type={f.type === "int" || f.type === "port" ? "number" : "text"}
                    min={f.min_value ?? undefined}
                    max={f.max_value ?? undefined}
                    value={values[f.name] === null || values[f.name] === undefined ? "" : String(values[f.name])}
                    onChange={(e) =>
                      setField(
                        f.name,
                        f.type === "int" || f.type === "port"
                          ? e.target.value === ""
                            ? null
                            : Number(e.target.value)
                          : e.target.value,
                      )
                    }
                  />
                )}
              </div>
            ))}
          </div>
        ) : (
          <div>
            <textarea
              aria-label="Configuration JSON"
              className="h-56 w-full rounded-lg border border-line-2 bg-background p-3 font-mono text-xs"
              value={jsonText}
              onChange={(e) => {
                setJsonText(e.target.value);
                // Validation à la saisie — erreurs précises (spec §7).
                try {
                  JSON.parse(e.target.value);
                  setJsonError(null);
                } catch (err) {
                  setJsonError((err as SyntaxError).message);
                }
              }}
              spellCheck={false}
            />
            {jsonError && (
              <p className="mt-1 text-xs text-red-500" role="alert">
                JSON invalide : {jsonError}
              </p>
            )}
            <div className="mt-2 flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleFormat}>
                Formater
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setMode("guided")}>
                Revenir au mode guidé
              </Button>
            </div>
          </div>
        )}

        {/* Résultat du test — fourni par le Core (section 6 de la spec) */}
        {testResult && (
          <div
            className={`rounded-lg border p-3 text-sm ${
              testResult.ok ? "border-green-soft bg-green-soft" : "border-red-soft bg-red-soft"
            }`}
            role="status"
          >
            <p className="flex items-center gap-2 font-medium">
              {testResult.ok ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-500" />
              )}
              {testResult.ok ? "Connexion validée" : `Test en échec (niveau : ${testResult.level})`}
            </p>
            <ul className="mt-1 space-y-0.5 text-xs text-muted-foreground">
              {testResult.checks.map((c, i) => (
                <li key={i}>
                  {c.kind} : {c.detail}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex justify-between pt-2">
          <Button
            variant="outline"
            onClick={() => {
              setTestResult(null);
              testMutation.mutate();
            }}
            disabled={testMutation.isPending}
          >
            {testMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Tester la connexion"
            )}
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Annuler
            </Button>
            <Button onClick={handleSave} disabled={configureMutation.isPending}>
              {configureMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Enregistrer"
              )}
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
