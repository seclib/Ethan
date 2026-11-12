"use client";

/**
 * ModelHub — Cockpit unifié de découverte et gestion des modèles IA dans ETHAN.
 *
 * Onglets : Installed · Discover · Downloads
 *
 * Discovery permet :
 * - recherche (terme libre, Hugging Face, catalogue)
 * - source (curated, huggingface, local)
 * - capacités (use_case, capabilities tags)
 * - taille (paramètres en B, empreinte RAM estimée)
 * - compatibilité (badge d'adéquation matérielle déterministe)
 * - méthode recommandée (Ollama GGUF, Safetensors vLLM, Cloud API...)
 * - Installer (déclenchement via Core)
 * - Utiliser (sélection du modèle comme moteur actif pour les conversations)
 *
 * Les détails techniques restent dans le tiroir "Advanced".
 * Aucune logique métier dans le frontend : le Core reste la source de vérité.
 */

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Cpu, Search, Download, Package, ChevronDown, ChevronUp,
  CheckCircle2, AlertTriangle, AlertCircle, XCircle,
  Loader2, RefreshCw, HardDrive, Activity,
  ShieldCheck, Info, Play, Check, Zap, Layers,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Progress } from "@/components/ui/progress";
import { useModelHub } from "@/components/features/models/hooks/use-model-hub";
import { useModelStore } from "@/store/model.store";
import type {
  HubModel,
  InstalledModel,
  HardwareInfo,
  DownloadItem,
  ModelInspection,
} from "@/lib/api/models";

type HubTab = "installed" | "discover" | "downloads";

const TABS: Array<{
  id: HubTab;
  label: string;
  icon: React.ComponentType<{ size?: number | string; className?: string }>;
}> = [
  { id: "installed", label: "Installed", icon: Package },
  { id: "discover", label: "Discover", icon: Search },
  { id: "downloads", label: "Downloads", icon: Download },
];

// ── Compatibility badge ─────────────────────────────────────────────────

function CompatBadge({ status, label }: { status: string; label: string }) {
  const variant =
    status === "compatible" ? "success"
    : status === "compatible_with_constraints" ? "warning"
    : status === "incompatible" ? "error"
    : "dim";

  const Icon =
    status === "compatible" ? ShieldCheck
    : status === "compatible_with_constraints" ? AlertTriangle
    : status === "incompatible" ? XCircle
    : Info;

  return (
    <Badge variant={variant} size="sm" className="gap-1">
      <Icon size={10} />
      {label}
    </Badge>
  );
}

// ── Installed tab ───────────────────────────────────────────────────────

function InstalledTab({
  models,
  loading,
  error,
  onRefresh,
  hardware,
  runtimeStatus,
  runtimesLoading,
  onRefreshRuntimes,
  onUseModel,
  activeModel,
}: {
  models: InstalledModel[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  hardware?: HardwareInfo;
  runtimeStatus?: string;
  runtimesLoading: boolean;
  onRefreshRuntimes: () => void;
  onUseModel: (provider: string, modelId: string) => void;
  activeModel: string;
}) {
  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (error) return <p className="py-8 text-center text-sm text-red">Erreur : {error}</p>;

  return (
    <div className="space-y-4">
      {/* Hardware + Runtime summary */}
      <div className="flex flex-wrap gap-3">
        {hardware && (
          <Card variant="flat" className="flex-1 min-w-[220px] !py-3">
            <CardContent className="!px-3 flex items-center gap-3">
              <HardDrive size={18} className="text-foreground-tertiary shrink-0" />
              <div className="text-xs space-y-0.5">
                <div className="font-medium text-foreground">
                  {hardware.gpu_count > 0
                    ? `${hardware.gpu_name} · ${hardware.gpu_vram_gb} Go VRAM`
                    : "CPU uniquement"}
                </div>
                <div className="text-foreground-tertiary">
                  RAM : {hardware.total_ram_gb} Go · {hardware.cpu_cores} cœurs
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        <Card variant="flat" className="min-w-[160px] !py-3">
          <CardContent className="!px-3 flex items-center gap-3">
            <Activity size={18} className="text-foreground-tertiary shrink-0" />
            <div className="text-xs">
              <div className="font-medium text-foreground flex items-center gap-1.5">
                Runtimes
                {runtimesLoading
                  ? <Loader2 size={12} className="animate-spin" />
                  : (
                    <Badge
                      variant={runtimeStatus === "healthy" ? "success" : runtimeStatus === "degraded" ? "warning" : "dim"}
                      size="sm"
                    >
                      {runtimeStatus ?? "inconnu"}
                    </Badge>
                  )}
              </div>
            </div>
            <Button variant="ghost" size="sm" className="ml-auto !h-6 !w-6 !p-0" onClick={onRefreshRuntimes}>
              <RefreshCw size={12} />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Installed models list */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">
          {models.length} modèle{models.length !== 1 ? "s" : ""} installé{models.length !== 1 ? "s" : ""}
        </h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} className="gap-1.5">
          <RefreshCw size={12} /> Actualiser
        </Button>
      </div>

      {models.length === 0 ? (
        <p className="py-8 text-center text-sm text-foreground-tertiary">
          Aucun modèle installé. Utilisez l&apos;onglet Discover pour en trouver.
        </p>
      ) : (
        <div className="space-y-1.5">
          {models.map((m) => {
            const isCurrent = activeModel === m.id || activeModel === m.name;
            return (
              <div
                key={`${m.provider}::${m.id}`}
                className="flex items-center gap-3 rounded-lg border border-line-1 px-3.5 py-2.5 hover:bg-surface transition-colors"
              >
                <Cpu size={16} className="text-foreground-tertiary shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground truncate">{m.name}</span>
                    {isCurrent && (
                      <Badge variant="accent" size="sm" className="gap-1">
                        <Check size={10} /> Actif
                      </Badge>
                    )}
                  </div>
                  <div className="text-[11px] text-foreground-tertiary mt-0.5">
                    {m.provider} · {m.source} · ctx {m.context_length}
                  </div>
                </div>
                <div className="flex gap-1 shrink-0">
                  {(m.capabilities || []).map((c) => (
                    <Badge key={c} variant="dim" size="sm">{c}</Badge>
                  ))}
                </div>
                <Badge variant={m.is_local ? "accent" : "default"} size="sm">
                  {m.is_local ? "local" : "cloud"}
                </Badge>
                <Button
                  size="sm"
                  variant={isCurrent ? "outline" : "default"}
                  onClick={() => onUseModel(m.provider, m.id)}
                  className="gap-1.5 shrink-0"
                >
                  <Play size={12} />
                  {isCurrent ? "Utiliser" : "Utiliser"}
                </Button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Discover tab ────────────────────────────────────────────────────────

function DiscoverTab({
  query,
  onQueryChange,
  source,
  onSourceChange,
  useCase,
  onUseCaseChange,
  results,
  loading,
  error,
  onSearch,
  onInstall,
  onUseModel,
  onInspect,
  inspection,
  isInspecting,
  inspectingModel,
  isInstalling,
  installingModel,
  activeModel,
}: {
  query: string;
  onQueryChange: (q: string) => void;
  source: string;
  onSourceChange: (s: string) => void;
  useCase: string;
  onUseCaseChange: (u: string) => void;
  results: HubModel[];
  loading: boolean;
  error: string | null;
  onSearch: () => void;
  onInstall: (modelId: string, provider?: string) => void;
  onUseModel: (provider: string, modelId: string) => void;
  onInspect: (modelId: string) => void;
  inspection: ModelInspection | null;
  isInspecting: boolean;
  inspectingModel: string | null;
  isInstalling: boolean;
  installingModel: string | null;
  activeModel: string;
}) {
  const [expandedAdvanced, setExpandedAdvanced] = React.useState<Record<string, boolean>>({});
  // Presentation-only filters (no business logic — the Core already computed
  // compatibility, method and sizes; the UI only narrows the displayed list).
  const [capFilter, setCapFilter] = React.useState<string>("all");
  const [sizeFilterLocal, setSizeFilterLocal] = React.useState<string>("all");
  const [compatFilter, setCompatFilter] = React.useState<string>("all");

  const filteredResults = React.useMemo(() => {
    return results.filter((model) => {
      if (capFilter !== "all") {
        const tags = [...(model.capabilities ?? []), model.use_case ?? ""].map((t) => t.toLowerCase());
        if (!tags.some((t) => t.includes(capFilter))) return false;
      }
      if (sizeFilterLocal !== "all") {
        const p = model.params_b ?? 0;
        if (sizeFilterLocal === "xs" && !(p > 0 && p <= 3)) return false;
        if (sizeFilterLocal === "s" && !(p > 3 && p <= 8)) return false;
        if (sizeFilterLocal === "l" && !(p > 8)) return false;
      }
      if (compatFilter !== "all" && model.compatibility?.status !== compatFilter) return false;
      return true;
    });
  }, [results, capFilter, sizeFilterLocal, compatFilter]);

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-foreground-tertiary" />
          <Input
            className="pl-8"
            placeholder="Rechercher un modèle (ex: qwen2.5, llama, mistral…)"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") onSearch(); }}
          />
        </div>
        <select
          value={source}
          onChange={(e) => onSourceChange(e.target.value)}
          className="rounded-[var(--radius-sm)] border border-line-2 bg-background px-3 py-2 text-sm text-foreground"
          aria-label="Filtrer par source"
        >
          <option value="all">Toutes les sources</option>
          <option value="curated">Catalogue ETHAN</option>
          <option value="local">Catalogue local (alias)</option>
          <option value="huggingface">Hugging Face</option>
        </select>
        <select
          value={useCase}
          onChange={(e) => onUseCaseChange(e.target.value)}
          className="rounded-[var(--radius-sm)] border border-line-2 bg-background px-3 py-2 text-sm text-foreground"
          aria-label="Filtrer par usage"
        >
          <option value="">Tous les usages</option>
          <option value="general">Général</option>
          <option value="chat">Chat</option>
          <option value="coding">Code</option>
          <option value="reasoning">Raisonnement</option>
        </select>
        <Button onClick={onSearch} disabled={loading} className="gap-1.5">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          Rechercher
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-soft bg-red-soft/30 px-3 py-2 text-sm text-red">
          <AlertCircle size={14} className="inline mr-1.5" />
          {error}
        </div>
      )}

      {/* Filtres de présentation : capacités · taille · compatibilité (aucune logique métier) */}
      <div className="flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
          Capacités
          <select
            value={capFilter}
            onChange={(e) => setCapFilter(e.target.value)}
            className="rounded-md border border-border bg-background px-1.5 py-1 text-xs"
            aria-label="Filtrer par capacités"
          >
            <option value="all">Toutes</option>
            <option value="chat">Chat</option>
            <option value="code">Code</option>
            <option value="reasoning">Raisonnement</option>
            <option value="vision">Vision</option>
            <option value="embed">Embedding</option>
          </select>
        </label>
        <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
          Taille
          <select
            value={sizeFilterLocal}
            onChange={(e) => setSizeFilterLocal(e.target.value)}
            className="rounded-md border border-border bg-background px-1.5 py-1 text-xs"
            aria-label="Filtrer par taille"
          >
            <option value="all">Toutes</option>
            <option value="xs">≤ 3B (léger)</option>
            <option value="s">3–8B (moyen)</option>
            <option value="l">&gt; 8B (lourd)</option>
          </select>
        </label>
        <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
          Compatibilité
          <select
            value={compatFilter}
            onChange={(e) => setCompatFilter(e.target.value)}
            className="rounded-md border border-border bg-background px-1.5 py-1 text-xs"
            aria-label="Filtrer par compatibilité"
          >
            <option value="all">Toutes</option>
            <option value="compatible">Compatible</option>
            <option value="compatible_with_constraints">Avec contraintes</option>
            <option value="incompatible">Incompatible</option>
            <option value="insufficient_info">Info insuffisante</option>
          </select>
        </label>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : results.length === 0 ? (
        <p className="py-8 text-center text-sm text-foreground-tertiary">
          {query ? "Aucun résultat. Essayez un autre terme de recherche." : "Entrez un terme de recherche pour découvrir des modèles."}
        </p>
      ) : filteredResults.length === 0 ? (
        <p className="py-8 text-center text-sm text-foreground-tertiary">
          Aucun résultat ne correspond aux filtres sélectionnés.
        </p>
      ) : (
        <div className="space-y-2">
          {filteredResults.map((model) => {
            const compat = model.compatibility;
            const isAdvOpen = !!expandedAdvanced[model.id];
            const isThisInstalling = isInstalling && installingModel === model.id;
            const isReady = model.is_installed;
            const isCurrent = activeModel === model.id || activeModel === model.name;

            return (
              <div
                key={model.id}
                className="flex flex-col rounded-lg border border-line-1 px-4 py-3 transition-colors hover:border-line-2"
              >
                <div className="flex items-center gap-3">
                  <Download size={16} className="text-foreground-tertiary shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-foreground truncate">
                        {model.name || model.id}
                      </span>
                      {compat && (
                        <CompatBadge status={compat.status} label={compat.status_label} />
                      )}
                      <Badge variant="dim" size="sm">{model.source}</Badge>
                      {model.use_case && (
                        <Badge variant="secondary" size="sm">{model.use_case}</Badge>
                      )}
                      {compat?.execution_method && (
                        <Badge variant="default" size="sm" className="gap-1 text-[10px]">
                          <Zap size={10} className="text-accent" />
                          {compat.execution_method}
                        </Badge>
                      )}
                    </div>
                    <div className="text-[11px] text-foreground-tertiary mt-1 flex items-center gap-2 flex-wrap">
                      <span>{model.description}</span>
                      {model.params_b > 0 && (
                        <span className="font-medium text-foreground-secondary">
                          · {model.params_b}B params (~{compat?.ram_required_gb ?? 0} Go RAM)
                        </span>
                      )}
                      {model.formats_available?.length > 0 && (
                        <span>· {model.formats_available.join(", ")}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {/* Advanced toggle */}
                    <button
                      type="button"
                      onClick={() => { onInspect(model.id); setExpandedAdvanced(prev => ({ ...prev, [model.id]: !prev[model.id] })); }}
                      className="text-[11px] px-2 py-1 rounded flex items-center gap-1 text-foreground-tertiary hover:text-foreground-secondary transition-colors"
                    >
                      Advanced {isAdvOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>

                    {/* Action buttons: Installer and/or Utiliser */}
                    {isReady ? (
                      <Button
                        size="sm"
                        variant={isCurrent ? "outline" : "default"}
                        onClick={() => onUseModel(model.provider || compat?.recommended_runtime || "ollama", model.id)}
                        className="gap-1.5"
                      >
                        <Play size={12} />
                        Utiliser
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => onInstall(model.id, compat?.recommended_runtime)}
                        disabled={isInstalling || (compat && !compat.compatible)}
                        className="gap-1.5"
                      >
                        {isThisInstalling ? (
                          <><Loader2 size={12} className="animate-spin" /> Installation…</>
                        ) : (
                          <><Download size={12} /> Installer</>
                        )}
                      </Button>
                    )}
                  </div>
                </div>

                {/* Advanced panel — inspection Core /inspect (formats, gating, méthode) */}
                {isAdvOpen && compat && (
                  <div className="mt-3 rounded-lg bg-surface p-3 text-[11px] text-foreground-secondary border border-line-1">
                    {isInspecting && inspectingModel === model.id && (
                      <p className="mb-2 flex items-center gap-1.5"><Loader2 size={12} className="animate-spin" /> Inspection Core en cours…</p>
                    )}
                    {inspection && inspectingModel === model.id && (
                      <div className="mb-2 flex flex-wrap gap-1.5">
                        <Badge variant="dim" size="sm">Formats : {inspection.formats_available?.join(", ") || "N/A"}</Badge>
                        {inspection.is_gated && <Badge variant="warning" size="sm">Gated HF (token requis)</Badge>}
                        <Badge variant={inspection.can_run ? "success" : "error"} size="sm">{inspection.can_run ? "Exécutable" : "Non exécutable"} — {inspection.method}</Badge>
                        {!inspection.conversion_supported && <Badge variant="dim" size="sm">Sans conversion</Badge>}
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
                      <div><strong>Runtime recommandé :</strong> {compat.recommended_runtime}</div>
                      <div><strong>Méthode d&apos;exécution :</strong> {compat.execution_method}</div>
                      <div><strong>RAM requise :</strong> ~{compat.ram_required_gb} Go</div>
                      <div><strong>VRAM requise :</strong> ~{compat.vram_required_gb} Go</div>
                      <div><strong>Vitesse estimée :</strong> {compat.estimated_speed_tps ? `${compat.estimated_speed_tps} tok/s` : "Non estimée"}</div>
                      <div><strong>Runtimes compatibles :</strong> {compat.supported_runtimes?.join(", ") || "N/A"}</div>
                      {inspection && inspectingModel === model.id && inspection.reason && (
                        <div className="col-span-2"><strong>Inspection Core :</strong> {inspection.reason}</div>
                      )}
                      <div className="col-span-2"><strong>Détail d&apos;adéquation :</strong> {compat.reason}</div>
                      {compat.recommendation && (
                        <div className="col-span-2"><strong>Recommandation :</strong> {compat.recommendation}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Downloads tab ───────────────────────────────────────────────────────

function DownloadsTab({
  downloads,
  loading,
  onRefresh,
}: {
  downloads: DownloadItem[];
  loading: boolean;
  onRefresh: () => void;
}) {
  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">
          {downloads.length} téléchargement{downloads.length !== 1 ? "s" : ""}
        </h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} className="gap-1.5">
          <RefreshCw size={12} /> Actualiser
        </Button>
      </div>

      {downloads.length === 0 ? (
        <div className="py-12 text-center">
          <Download size={32} className="mx-auto mb-3 text-foreground-tertiary" />
          <p className="text-sm text-foreground-secondary">Aucun téléchargement enregistré.</p>
          <p className="mt-1 text-[11px] text-foreground-tertiary">
            Les téléchargements Hugging Face ou pulls Ollama apparaîtront ici avec leur statut.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {downloads.map((d) => {
            const isFinished = d.status === "completed";
            const isFailed = d.status === "failed";
            const isActive = d.status === "downloading" || d.status === "starting";

            const statusBadgeVariant =
              isFinished ? "success" : isFailed ? "error" : isActive ? "accent" : "dim";

            const statusLabel =
              d.status === "completed" ? "Terminé"
              : d.status === "downloading" ? "En cours"
              : d.status === "starting" ? "Démarrage"
              : "Échoué";

            return (
              <div
                key={d.id}
                className="flex flex-col gap-2 rounded-lg border border-line-1 p-3.5 transition-colors hover:border-line-2"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <Download size={16} className="text-foreground-tertiary shrink-0" />
                    <span className="text-sm font-medium text-foreground truncate">{d.repo_id}</span>
                    <Badge variant={statusBadgeVariant} size="sm">{statusLabel}</Badge>
                    <Badge variant="dim" size="sm">{d.runtime}</Badge>
                  </div>
                  <span className="text-xs font-mono text-foreground-secondary shrink-0">
                    {Math.round(d.percent)}%
                  </span>
                </div>

                <Progress
                  value={d.percent}
                  size="sm"
                  variant={isFinished ? "success" : isFailed ? "error" : "default"}
                />

                {d.error && (
                  <p className="text-xs text-red mt-1">
                    <AlertCircle size={12} className="inline mr-1" />
                    {d.error}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────────

export function ModelHub() {
  const router = useRouter();
  const [tab, setTab] = React.useState<HubTab>("installed");
  const [installingModel, setInstallingModel] = React.useState<string | null>(null);
  const [inspectingModel, setInspectingModel] = React.useState<string | null>(null);

  const hub = useModelHub();
  const activeModel = useModelStore((s) => s.selectedModel);
  const setSelection = useModelStore((s) => s.setSelection);

  const handleInstall = React.useCallback(async (modelId: string, provider?: string) => {
    setInstallingModel(modelId);
    try {
      await hub.installModel({ model: modelId, provider });
      hub.refetchInstalled();
    } catch {
      // Error handled in store/mutation
    } finally {
      setInstallingModel(null);
    }
  }, [hub]);

  const handleUseModel = React.useCallback((provider: string, modelId: string) => {
    setSelection(provider, modelId);
    router.push("/");
  }, [setSelection, router]);

  // Gating Utiliser : un modèle non installé n'est sélectionnable qu'après
  // inspection Core confirmant can_run (le Core reste seul juge d'exécutabilité).
  const handleGatedUseModel = React.useCallback((provider: string, modelId: string) => {
    const hit = hub.discoverResults.find((m) => m.id === modelId);
    if (hit && !hit.is_installed) {
      setInspectingModel(modelId);
      void hub.handleInspect(modelId).then((res) => {
        if (res && res.can_run) handleUseModel(provider, modelId);
      });
      return;
    }
    handleUseModel(provider, modelId);
  }, [hub, handleUseModel]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Tab bar */}
      <div className="mb-3 flex items-center gap-1 border-b border-line-1 pb-2 px-1">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            aria-current={tab === id ? "page" : undefined}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors ${
              tab === id
                ? "bg-primary/10 text-primary font-medium"
                : "text-foreground-secondary hover:bg-muted"
            }`}
            onClick={() => setTab(id)}
          >
            <Icon size={14} className={tab === id ? "text-primary" : "text-muted-foreground"} />
            {label}
            {id === "installed" && hub.installed.length > 0 && (
              <span className="ml-1 rounded-full bg-bg-3 px-1.5 py-0.5 text-[10px] font-medium text-foreground-tertiary">
                {hub.installed.length}
              </span>
            )}
            {id === "downloads" && hub.downloads.length > 0 && (
              <span className="ml-1 rounded-full bg-bg-3 px-1.5 py-0.5 text-[10px] font-medium text-foreground-tertiary">
                {hub.downloads.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="min-h-0 flex-1 overflow-y-auto px-1">
        {tab === "installed" && (
          <InstalledTab
            models={hub.installed}
            loading={hub.installedLoading}
            error={hub.installedError}
            onRefresh={() => hub.refetchInstalled()}
            hardware={hub.hardware}
            runtimeStatus={hub.runtimeHealth?.status}
            runtimesLoading={hub.runtimesLoading}
            onRefreshRuntimes={() => hub.refetchRuntimes()}
            onUseModel={handleUseModel}
            activeModel={activeModel}
          />
        )}
        {tab === "discover" && (
          <DiscoverTab
            query={hub.discoverQuery}
            onQueryChange={hub.setDiscoverQuery}
            source={hub.discoverSource}
            onSourceChange={hub.setDiscoverSource}
            useCase={hub.discoverUseCase}
            onUseCaseChange={hub.setDiscoverUseCase}
            results={hub.discoverResults}
            loading={hub.isDiscovering}
            error={hub.discoverError}
            onSearch={() => hub.handleDiscover()}
            onInstall={handleInstall}
            onUseModel={handleGatedUseModel}
            onInspect={(id) => { setInspectingModel(id); hub.handleInspect(id); }}
            inspection={hub.inspection}
            isInspecting={hub.isInspecting}
            inspectingModel={inspectingModel}
            isInstalling={hub.isInstalling}
            installingModel={installingModel}
            activeModel={activeModel}
          />
        )}
        {tab === "downloads" && (
          <DownloadsTab
            downloads={hub.downloads}
            loading={hub.downloadsLoading}
            onRefresh={() => hub.refetchDownloads()}
          />
        )}
      </div>
    </div>
  );
}
