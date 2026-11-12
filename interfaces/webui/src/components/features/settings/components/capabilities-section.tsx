"use client";

/**
 * ETHAN WebUI — section Settings ▸ Capabilities.
 *
 * Interface PASSIVE du gestionnaire de capacités : catalogue, états réels,
 * actions et diagnostics proviennent exclusivement d'ETHAN Core
 * (/v1/components — core/capability_manager). Aucune logique d'installation.
 *
 * Les catégories (AI Providers, Models, Embedding, Vector Databases, Speech,
 * Integrations, Tools, Services) suivent la taxinomie de la spec ; seuls les
 * composants réellement enregistrés dans le Core sont affichés.
 */

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, Loader2, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { useUIStore } from "@/store/ui.store";
import {
  detectComponents,
  disableComponent,
  enableComponent,
  installComponent,
  listComponents,
  startComponent,
  stopComponent,
  type ComponentProvenance,
  type ComponentState,
  type ComponentStatus,
} from "@/lib/api/components";
import {
  ConfigureDialog,
  InstallDialog,
  UninstallDialog,
} from "./capability-dialogs";

/* ── Libellés d'état (section 2 — jamais un simple « installé ») ───────── */

const STATE_LABELS: Record<ComponentState, { label: string; variant: "success" | "info" | "warning" | "error" | "secondary" | "dim" | "accent" }> = {
  SUPPORTED: { label: "Available", variant: "dim" },
  NOT_INSTALLED: { label: "Not installed", variant: "dim" },
  INSTALLING: { label: "Installing…", variant: "info" },
  INSTALLED: { label: "Installed", variant: "secondary" },
  STARTING: { label: "Starting…", variant: "info" },
  RUNNING: { label: "Running", variant: "accent" },
  STOPPED: { label: "Stopped", variant: "warning" },
  UNHEALTHY: { label: "Unhealthy", variant: "warning" },
  CONFIGURATION_REQUIRED: { label: "Configuration required", variant: "warning" },
  READY: { label: "Ready", variant: "success" },
  UNINSTALLING: { label: "Uninstalling…", variant: "info" },
  ERROR: { label: "Error", variant: "error" },
};

/**
 * Catégories de la spec — seules celles avec composants réels apparaissent.
 * Miroir EXACT de CapabilityType (core/capability_manager/types.py) : un type
 * inconnu tombe dans « Autres », jamais réinventé ici.
 */
const TYPE_LABELS: Record<string, string> = {
  provider: "AI Providers",
  model: "Models",
  embedding: "Embedding",
  reranker: "Reranking",
  vector_database: "Vector Databases",
  stt_tts: "Speech / Transcription",
  runtime: "Services",
  service: "Services",
  integration: "Integrations",
  tool: "Tools",
  mcp_server: "MCP Servers",
  plugin: "Plugins",
  skill: "Skills",
};

/** Sources de provenance (miroir Core) — valeur inconnue affichée brute. */
const PROVENANCE_LABELS: Record<string, string> = {
  builtin: "Builtin ETHAN",
  official: "Officiel",
  community: "Communauté",
  custom: "Personnalisé",
};

const PROVENANCE_VARIANTS: Record<string, "secondary" | "info" | "gold" | "purple"> = {
  builtin: "secondary",
  official: "info",
  community: "gold",
  custom: "purple",
};

/** Titre de la pastille : où vérifier le composant — rien si le Core ne dit rien. */
function provenanceTitle(p: ComponentProvenance): string | undefined {
  const parts: string[] = [];
  if (p.url) parts.push(`Source : ${p.url}`);
  if (p.checksum) parts.push(`Empreinte : ${p.checksum}`);
  return parts.length > 0 ? parts.join("\n") : undefined;
}

const STATE_LABEL_FALLBACK = "Unknown";

function StateBadge({ state }: { state: ComponentState }) {
  const def = STATE_LABELS[state] ?? { label: STATE_LABEL_FALLBACK, variant: "dim" as const };
  return (
    <Badge variant={def.variant} data-testid="component-state">
      {def.label}
    </Badge>
  );
}

/* ── Carte d'un composant ──────────────────────────────────────────────── */

function CapabilityCard({
  component,
  onInstall,
  onConfigure,
  onUninstall,
}: {
  component: ComponentStatus;
  onInstall: () => void;
  onConfigure: () => void;
  onUninstall: () => void;
}) {
  const addToast = useUIStore((s) => s.addToast);
  const queryClient = useQueryClient();
  const [errorOpen, setErrorOpen] = React.useState(false);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["components"] });

  const onStopError = (err: unknown) =>
    addToast({
      type: "error",
      message: err instanceof Error ? err.message : "l'opération a échoué",
    });

  const stopMutation = useMutation({
    mutationFn: () => stopComponent(component.id),
    onSuccess: () => {
      addToast({ type: "success", message: `${component.name} arrêté` });
      invalidate();
    },
    onError: onStopError,
  });
  const startMutation = useMutation({
    mutationFn: () => startComponent(component.id),
    onSuccess: () => {
      addToast({ type: "success", message: `${component.name} démarré` });
      invalidate();
    },
    onError: onStopError,
  });
  const enableMutation = useMutation({
    mutationFn: () => enableComponent(component.id),
    onSuccess: () => {
      addToast({ type: "success", message: `${component.name} activé` });
      invalidate();
    },
    onError: onStopError,
  });
  const disableMutation = useMutation({
    mutationFn: () => disableComponent(component.id),
    onSuccess: () => {
      addToast({ type: "success", message: `${component.name} désactivé` });
      invalidate();
    },
    onError: onStopError,
  });
  const retryMutation = useMutation({
    // Retry : réinstalle si jamais installé, sinon redémarre (idempotent côté Core).
    mutationFn: async () => {
      if (component.installed_version) {
        await startComponent(component.id);
      } else {
        await installComponent(component.id);
      }
    },
    onSuccess: () => {
      addToast({ type: "success", message: `${component.name} relancé` });
      invalidate();
    },
    onError: (err) =>
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Relance échouée",
      }),
  });

  const busy = ["INSTALLING", "STARTING", "UNINSTALLING"].includes(component.state);
  const canStart = component.state === "INSTALLED" || component.state === "STOPPED";
  const canStop = ["RUNNING", "READY", "UNHEALTHY"].includes(component.state);
  const installed = component.state !== "NOT_INSTALLED" && component.state !== "SUPPORTED";
  const builtin = component.backend === "builtin";

  return (
    <div
      className="rounded-xl border border-line-2 bg-bg-1 p-4"
      data-testid={`component-card-${component.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-semibold text-foreground">{component.name}</h3>
            <StateBadge state={component.state} />
            {component.enabled && <Badge variant="accent">Active</Badge>}
            {component.provenance && (
              <Badge
                variant={PROVENANCE_VARIANTS[component.provenance.source] ?? "secondary"}
                size="sm"
                data-testid="component-provenance"
                title={provenanceTitle(component.provenance)}
              >
                {PROVENANCE_LABELS[component.provenance.source] ?? component.provenance.source}
              </Badge>
            )}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{component.description}</p>
          <p className="mt-1 text-xs text-foreground-tertiary">
            v{component.installed_version ?? component.version} · backend {component.backend}
          </p>
          {component.provenance &&
            (component.provenance.author || component.provenance.license) && (
              <p className="mt-0.5 text-xs text-foreground-tertiary">
                {`${component.provenance.author}${
                  component.provenance.author && component.provenance.license ? " · " : ""
                }${component.provenance.license}`}
              </p>
            )}
        </div>
      </div>

      {component.dependencies.length > 0 && (
        <p className="mt-2 text-xs text-muted-foreground">
          Dépend de :{" "}
          {component.dependencies.map((d) => (
            <Badge key={d.id} variant="secondary" size="sm" className="mr-1">
              {d.id}
            </Badge>
          ))}
        </p>
      )}
      {component.data_resources.length > 0 && (
        <p className="mt-1 text-xs text-muted-foreground">
          Données : {component.data_resources.map((r) => r.name).join(", ")}
        </p>
      )}

      {(component.state === "ERROR" || component.state === "UNHEALTHY") &&
        component.last_error && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-soft bg-red-soft p-2 text-xs text-red-500">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span className="break-all">{component.last_error}</span>
          </div>
        )}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {busy ? (
          <span className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> opération en cours…
          </span>
        ) : (
          <>
            {builtin ? (
              /* Composant intégré (spec §8) : prêt par construction —
                 seule la configuration est pertinente. */
              <>
                <Button size="sm" onClick={onConfigure}>
                  Configurer
                </Button>
              </>
            ) : (
              <>
            {!installed && (
              <Button size="sm" onClick={onInstall}>
                Installer
              </Button>
            )}
            {canStart && (
              <Button size="sm" onClick={() => startMutation.mutate()} disabled={startMutation.isPending}>
                Démarrer
              </Button>
            )}
            {canStop && (
              <Button size="sm" variant="secondary" onClick={() => stopMutation.mutate()} disabled={stopMutation.isPending}>
                Arrêter
              </Button>
            )}
            {installed && component.state !== "CONFIGURATION_REQUIRED" && (
              <Button size="sm" variant="outline" onClick={onConfigure}>
                Configurer
              </Button>
            )}
            {component.state === "CONFIGURATION_REQUIRED" && (
              <Button size="sm" onClick={onConfigure}>
                Configurer
              </Button>
            )}
            {component.state === "READY" && !component.enabled && (
              <Button size="sm" variant="ghost" onClick={() => enableMutation.mutate()} disabled={enableMutation.isPending}>
                Activer
              </Button>
            )}
            {component.state === "READY" && component.enabled && (
              <Button size="sm" variant="ghost" onClick={() => disableMutation.mutate()} disabled={disableMutation.isPending}>
                Désactiver
              </Button>
            )}
            {component.state === "ERROR" && (
              <>
                <Button size="sm" variant="outline" onClick={() => setErrorOpen(true)}>
                  Voir les détails
                </Button>
                <Button size="sm" onClick={() => retryMutation.mutate()} disabled={retryMutation.isPending}>
                  Réessayer
                </Button>
              </>
            )}
            {installed && (
              <Button size="sm" variant="ghost" className="text-red-500" onClick={onUninstall}>
                Désinstaller
              </Button>
            )}
              </>
            )}
          </>
        )}
      </div>

      {/* Détails d'erreur — dernière erreur connue du Core */}
      <Dialog open={errorOpen} onClose={() => setErrorOpen(false)} title={`Détails — ${component.name}`}>
        <div className="space-y-3 text-sm">
          <p className="text-xs uppercase tracking-wider text-foreground-tertiary">État</p>
          <StateBadge state={component.state} />
          <p className="text-xs uppercase tracking-wider text-foreground-tertiary">Dernière erreur</p>
          <pre className="max-h-56 overflow-auto rounded-lg border border-line-2 bg-bg-2 p-3 text-xs whitespace-pre-wrap">
            {component.last_error ?? "aucune"}
          </pre>
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => setErrorOpen(false)}>
              Fermer
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

/* ── Section complète : catalogue groupé par catégorie ─────────────────── */

export function CapabilitiesSection() {
  const addToast = useUIStore((s) => s.addToast);
  const queryClient = useQueryClient();
  const [installTarget, setInstallTarget] = React.useState<ComponentStatus | null>(null);
  const [configureTarget, setConfigureTarget] = React.useState<ComponentStatus | null>(null);
  const [uninstallTarget, setUninstallTarget] = React.useState<ComponentStatus | null>(null);

  // La liste inclut la détection Core (refresh=true) : états RÉELS uniquement.
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["components"],
    queryFn: () => listComponents(true),
    refetchInterval: 15000,
  });

  const detectMutation = useMutation({
    mutationFn: () => detectComponents(),
    onSuccess: () => {
      addToast({ type: "info", message: "Détection Core relancée" });
      queryClient.invalidateQueries({ queryKey: ["components"] });
    },
    onError: (err) =>
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Détection impossible",
      }),
  });

  const components = React.useMemo(
    () => data?.capabilities ?? [],
    [data],
  );
  const groups = React.useMemo(() => {
    const map = new Map<string, ComponentStatus[]>();
    for (const c of components) {
      const label = TYPE_LABELS[c.type] ?? "Autres";
      const list = map.get(label) ?? [];
      list.push(c);
      map.set(label, list);
    }
    return [...map.entries()];
  }, [components]);

  return (
    <div>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-foreground">Capacités</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Composants optionnels de l&apos;écosystème ETHAN : installer, configurer,
            tester, activer, désinstaller. Les états et la progression proviennent
            du Core — rien n&apos;est installé automatiquement.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => detectMutation.mutate()}
          disabled={detectMutation.isPending}
        >
          {detectMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Rafraîchir l&apos;état
        </Button>
      </div>

      {isLoading && (
        <p className="flex items-center gap-2 py-10 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Lecture du catalogue Core…
        </p>
      )}
      {isError && (
        <div className="rounded-lg border border-red-soft bg-red-soft p-4 text-sm text-red-500">
          Catalogue indisponible : {(error as Error).message}
        </div>
      )}

      {!isLoading && !isError && components.length === 0 && (
        <p className="py-10 text-sm text-muted-foreground">
          Aucun composant optionnel enregistré dans le Core.
        </p>
      )}

      <div className="space-y-8">
        {groups.map(([label, items]) => (
          <section key={label} aria-label={label}>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-foreground-tertiary">
              {label}
            </h2>
            <div className="grid gap-4 lg:grid-cols-2">
              {items.map((c) => (
                <CapabilityCard
                  key={c.id}
                  component={c}
                  onInstall={() => setInstallTarget(c)}
                  onConfigure={() => setConfigureTarget(c)}
                  onUninstall={() => setUninstallTarget(c)}
                />
              ))}
            </div>
          </section>
        ))}
      </div>

      {installTarget && (
        <InstallDialog
          component={installTarget}
          open
          onClose={() => setInstallTarget(null)}
          onCompleted={() => queryClient.invalidateQueries({ queryKey: ["components"] })}
        />
      )}
      {configureTarget && (
        <ConfigureDialog
          component={configureTarget}
          open
          onClose={() => setConfigureTarget(null)}
        />
      )}
      {uninstallTarget && (
        <UninstallDialog
          component={uninstallTarget}
          open
          onClose={() => setUninstallTarget(null)}
          onCompleted={() => queryClient.invalidateQueries({ queryKey: ["components"] })}
        />
      )}
    </div>
  );
}
