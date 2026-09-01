"use client";

/**
 * ETHAN WebUI — Settings Workspace
 *
 * Organized around ETHAN's real capabilities. Every section is backed by a
 * real Core/Runtime API endpoint: data is loaded live, mutations are real,
 * success and errors are surfaced as toasts, and state always reflects the
 * backend after save (react-query invalidation + refetch).
 *
 * Sections whose full management lives in dedicated workspaces (Knowledge,
 * Agents, Tools) show live backend state and link to the workspace — the
 * WebUI never duplicates Core business logic.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  testProviderConnection,
  setDefaultProvider,
  type Provider,
  type ProviderCreate,
  type ProviderUpdate,
} from "@/lib/api/providers";
import { listModels, toggleModel, type ModelInfo } from "@/lib/api/models";
import {
  getRagConfig,
  updateRagConfig,
  getRagStatus,
  type RagConfigResponse,
} from "@/lib/api/rag";
import { listSkills, toggleSkill, type Skill } from "@/lib/api/skills";
import { listAgents } from "@/lib/api/agents";
import {
  listTools,
  listToolServers,
  registerToolServer,
  updateToolServer,
  deleteToolServer,
  setToolServerStatus,
  type ToolServer,
  type CoreTool,
} from "@/lib/api/tools";
import { listRagDocuments } from "@/lib/api/knowledge";
import { useSettings } from "@/components/features/settings/hooks/use-settings";
import { useUIStore } from "@/store/ui.store";
import { useTheme } from "@/providers/theme-provider";
import {
  ACCENT_PRESETS,
  setStoredAccent,
  getActiveAccentId,
} from "@/lib/accent";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import {
  Settings,
  Palette,
  Cpu,
  Database,
  BookOpen,
  Zap,
  Sparkles,
  Bot,
  Wrench,
  Network,
  Plus,
  Play,
  Trash2,
  Edit3,
  Loader2,
  ExternalLink,
  ToggleLeft,
  ToggleRight,
  Save,
} from "lucide-react";

type Section =
  | "general"
  | "appearance"
  | "models"
  | "providers"
  | "knowledge"
  | "rag"
  | "skills"
  | "agents"
  | "tools"
  | "mcp";

const SECTIONS: { id: Section; label: string; icon: React.ReactNode }[] = [
  { id: "general", label: "General", icon: <Settings className="h-4 w-4" /> },
  { id: "appearance", label: "Appearance", icon: <Palette className="h-4 w-4" /> },
  { id: "models", label: "Models", icon: <Cpu className="h-4 w-4" /> },
  { id: "providers", label: "Providers", icon: <Database className="h-4 w-4" /> },
  { id: "knowledge", label: "Knowledge", icon: <BookOpen className="h-4 w-4" /> },
  { id: "rag", label: "RAG", icon: <Zap className="h-4 w-4" /> },
  { id: "skills", label: "Skills", icon: <Sparkles className="h-4 w-4" /> },
  { id: "agents", label: "Agents", icon: <Bot className="h-4 w-4" /> },
  { id: "tools", label: "Tools", icon: <Wrench className="h-4 w-4" /> },
  { id: "mcp", label: "MCP", icon: <Network className="h-4 w-4" /> },
];

export function SettingsWorkspace() {
  const [activeSection, setActiveSection] = React.useState<Section>("general");
  const [search, setSearch] = React.useState("");
  const [selectedProviderId, setSelectedProviderId] = React.useState<string | null>(null);

  // Section pilotée par le hash URL (#general, #appearance, …) : la sidebar
  // v3 ouvre directement « Interface » (/settings#appearance).
  React.useEffect(() => {
    const applyHash = () => {
      const h = window.location.hash.replace("#", "") as Section;
      if (SECTIONS.some((s) => s.id === h)) setActiveSection(h);
    };
    applyHash();
    window.addEventListener("hashchange", applyHash);
    return () => window.removeEventListener("hashchange", applyHash);
  }, []);

  return (
    <div className="flex h-full min-h-0">
      {/* Left panel: section navigation */}
      <div className="flex w-64 shrink-0 flex-col border-r border-line-1" style={{ background: "var(--panel)" }}>
        <div className="border-b border-line-1 px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground">Settings</h2>
        </div>
        <nav className="sidebar-inner custom-scrollbar" style={{ padding: "8px" }}>
          {SECTIONS.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={cn("list-item w-full", activeSection === section.id && "active")}
              style={{ width: "100%", border: "none", background: "transparent", textAlign: "left" }}
            >
              {section.icon}
              <span>{section.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Right panel: section content */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        {activeSection === "general" && <GeneralSection />}
        {activeSection === "appearance" && <AppearanceSection />}
        {activeSection === "models" && <ModelsSection />}
        {activeSection === "providers" && (
          <ProvidersSection
            selectedProviderId={selectedProviderId}
            onSelect={setSelectedProviderId}
          />
        )}
        {activeSection === "knowledge" && <KnowledgeSection />}
        {activeSection === "rag" && <RagSection />}
        {activeSection === "skills" && <SkillsSection />}
        {activeSection === "agents" && <AgentsSection />}
        {activeSection === "tools" && <ToolsCatalogueSection />}
        {activeSection === "mcp" && <McpServersSection />}
      </div>
    </div>
  );
}

/* ── Shared building blocks ─────────────────────────────────────── */

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-xl font-bold text-foreground">{title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

function SectionLoading() {
  return (
    <div className="flex h-full items-center justify-center py-16 text-foreground-tertiary">
      <Loader2 className="h-5 w-5 animate-spin" />
    </div>
  );
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={cn(
        "inline-block h-2 w-2 shrink-0 rounded-full",
        ok ? "bg-[var(--green)]" : "bg-[var(--red)]",
      )}
      title={ok ? "Disponible" : "Indisponible"}
    />
  );
}

function WorkspaceLink({ href, label }: { href: string; label: string }) {
  return (
    <a href={href}>
      <Button variant="secondary" size="sm">
        <ExternalLink className="h-3.5 w-3.5" />
        <span className="ml-1">{label}</span>
      </Button>
    </a>
  );
}

/* ── General — editable Core settings (/v1/settings) ────────────── */

function GeneralSection() {
  const { settings, isLoading, update, isUpdating } = useSettings();
  const addToast = useUIStore((s) => s.addToast);
  const [draft, setDraft] = React.useState<Record<string, Record<string, unknown>> | null>(null);

  // Re-seed the local draft whenever backend state changes.
  React.useEffect(() => {
    if (settings) {
      setDraft({
        system: { ...(settings.system as any) },
        llm: { ...(settings.llm as any) },
      });
    }
  }, [settings]);

  const dirty =
    !!draft &&
    !!settings &&
    (JSON.stringify(draft.system) !== JSON.stringify(settings.system) ||
      JSON.stringify(draft.llm) !== JSON.stringify(settings.llm));

  const handleSave = async () => {
    if (!draft || !dirty) return;
    const result = await update({ system: draft.system, llm: draft.llm } as any);
    if (!result.error) {
      addToast({ type: "success", message: "Configuration enregistrée" });
    }
  };

  const setField = (sectionKey: string, key: string, value: unknown) => {
    setDraft((prev) =>
      prev ? { ...prev, [sectionKey]: { ...prev[sectionKey], [key]: value } } : prev,
    );
  };

  if (isLoading || !settings || !draft) return <SectionLoading />;

  return (
    <div className="p-6">
      <SectionHeader
        title="Settings"
        description="Configuration générale et gouvernance du système"
      />
      {(["system", "llm"] as const).map((sectionKey) => (
        <div key={sectionKey} className="mb-8">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground-tertiary">
            {sectionKey === "system" ? "System" : "LLM"}
          </h3>
          <p className="mb-3 mt-1 text-xs text-foreground-tertiary">
            {sectionKey === "system"
              ? "Comportement général d'ETHAN : mode de fonctionnement, limites et gouvernance."
              : "Paramètres par défaut des modèles de langage utilisés par le Core."}
          </p>
          <div className="space-y-3">
            {Object.entries(draft[sectionKey] ?? {}).map(([k, v]) => (
              <div key={k} className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3">
                <span className="text-sm text-foreground-secondary font-mono">{k}</span>
                {typeof v === "boolean" ? (
                  <button
                    type="button"
                    onClick={() => setField(sectionKey, k, !v)}
                    className="text-accent"
                    aria-label={`Toggle ${k}`}
                  >
                    {v ? <ToggleRight className="h-5 w-5" /> : <ToggleLeft className="h-5 w-5" />}
                  </button>
                ) : typeof v === "number" ? (
                  <Input
                    type="number"
                    className="w-48"
                    value={String(v)}
                    step="any"
                    onChange={(e) => setField(sectionKey, k, Number(e.target.value))}
                  />
                ) : (
                  <Input
                    className="w-48"
                    value={String(v)}
                    onChange={(e) => setField(sectionKey, k, e.target.value)}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="flex justify-end">
        <Button variant="primary" onClick={handleSave} disabled={!dirty || isUpdating}>
          {isUpdating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          <span className="ml-1">Enregistrer</span>
        </Button>
      </div>
    </div>
  );
}

/* ── Appearance — WebUI preferences (theme, accent, interface) ──── */

const THEME_OPTIONS: { id: "dark" | "light" | "system" | "high-contrast" | "oled"; label: string }[] = [
  { id: "dark", label: "Dark" },
  { id: "light", label: "Light" },
  { id: "system", label: "System" },
  { id: "oled", label: "OLED" },
  { id: "high-contrast", label: "High contrast" },
];

function AppearanceSection() {
  const { theme, setTheme } = useTheme();
  const sidebarExpanded = useUIStore((s) => s.sidebarExpanded);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
    const [accentId, setAccentId] = React.useState<string>("ethan");

  React.useEffect(() => {
    setAccentId(getActiveAccentId());
  }, []);

  const handleAccent = (preset: (typeof ACCENT_PRESETS)[number]) => {
    setStoredAccent(preset);
    setAccentId(getActiveAccentId());
  };

  return (
    <div className="p-6">
      <SectionHeader
        title="Appearance"
        description="Thème, couleur d'accent et préférences d'interface"
      />

      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-tertiary">Thème</h3>
      <div className="flex flex-wrap gap-2">
        {THEME_OPTIONS.map((opt) => (
          <Button
            key={opt.id}
            size="sm"
            variant={theme === opt.id ? "primary" : "secondary"}
            onClick={() => setTheme(opt.id)}
          >
            {opt.label}
          </Button>
        ))}
      </div>

      <h3 className="mb-3 mt-8 text-xs font-semibold uppercase tracking-wider text-foreground-tertiary">Accent</h3>
      <div className="flex flex-wrap gap-3">
        {ACCENT_PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            onClick={() => handleAccent(preset)}
            title={preset.label}
            aria-label={`Accent ${preset.label}`}
            className={cn(
              "flex h-9 items-center gap-2 rounded-lg border px-3 text-sm",
              accentId === preset.id
                ? "border-accent ring-1 ring-accent"
                : "border-line-2 hover:border-line-3",
            )}
          >
            <span
              className="inline-block h-4 w-4 rounded-full"
              style={{
                background: preset.rgb ? `rgb(${preset.rgb})` : "var(--accent)",
              }}
            />
            <span className="text-foreground-secondary">{preset.label}</span>
          </button>
        ))}
      </div>

      <h3 className="mb-3 mt-8 text-xs font-semibold uppercase tracking-wider text-foreground-tertiary">Interface</h3>
      <div className="flex max-w-xl items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3">
        <span className="text-sm text-foreground-secondary">Sidebar étendue</span>
        <button type="button" onClick={toggleSidebar} className="text-accent" aria-label="Toggle sidebar">
          {sidebarExpanded ? <ToggleRight className="h-5 w-5" /> : <ToggleLeft className="h-5 w-5" />}
        </button>
      </div>
    </div>
  );
}

/* ── Models — live model catalogue (/models) ────────────────────── */

function ModelsSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [search, setSearch] = React.useState("");

  const { data: models = [], isLoading } = useQuery({
    queryKey: ["settings-models"],
    queryFn: () => listModels({ include_custom: true }),
  });

  const toggleMutation = useMutation({
    mutationFn: (id: string) => toggleModel(id),
    onSuccess: (m) => {
      queryClient.invalidateQueries({ queryKey: ["settings-models"] });
      addToast({ type: "success", message: `Modèle « ${m.name} » mis à jour` });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec du toggle" }),
  });

  const filtered = models.filter(
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.model.toLowerCase().includes(search.toLowerCase()) ||
      m.provider.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="p-6">
      <SectionHeader
        title="Models"
        description="Catalogue de modèles découverts et personnalisés"
      />

      {/* Navigation secondaire : gestion complète sur la page dédiée */}
      <div className="mb-4">
        <WorkspaceLink href="/models" label="Ouvrir le workspace Models" />
      </div>

      <div className="mb-4 max-w-md">
        <Input placeholder="Rechercher un modèle…" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {isLoading ? (
        <SectionLoading />
      ) : filtered.length === 0 ? (
        <p className="text-sm text-foreground-tertiary">Aucun modèle trouvé.</p>
      ) : (
                <div className="space-y-2">
          {filtered.map((m: ModelInfo) => (
            <div
              key={m.id}
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <StatusDot ok={m.is_available} />
                  <span className="truncate text-sm font-medium text-foreground">{m.name}</span>
                  {m.is_custom && (
                    <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] uppercase text-accent">custom</span>
                  )}
                  {m.source === "discovered" && (
                    <span className="rounded-full bg-foreground-tertiary/10 px-2 py-0.5 text-[10px] uppercase text-foreground-tertiary">decouvert</span>
                  )}
                </div>
                <p className="mt-0.5 truncate font-mono text-xs text-foreground-tertiary">
                  {m.provider} · {m.model} · {m.context_length.toLocaleString()} tokens
                </p>
              </div>
              <div className="flex items-center gap-2">
                {m.is_custom ? (
                  <>
                    <span className="text-xs text-foreground-tertiary">
                      {m.is_available ? "Activé" : "Désactivé"}
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => toggleMutation.mutate(m.id)}
                      disabled={toggleMutation.isPending}
                      aria-label={`Toggle ${m.name}`}
                      title={m.is_available ? "Désactiver ce modèle" : "Activer ce modèle"}
                    >
                      {toggleMutation.isPending && toggleMutation.variables === m.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <ToggleRight
                          className={cn(
                            "h-5 w-5",
                            m.is_available ? "text-accent" : "text-foreground-tertiary",
                          )}
                        />
                      )}
                    </Button>
                  </>
                ) : (
                  <span
                    className={cn(
                      "text-xs",
                      m.is_available ? "text-foreground-tertiary" : "text-amber-500",
                    )}
                    title={`Modèle détecté automatiquement via ${m.provider} — son état dépend de la disponibilité du provider`}
                  >
                    Géré par {m.provider} · {m.is_available ? "Disponible" : "Provider hors ligne"}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Knowledge — live backend state + workspace link ───────────── */

function KnowledgeSection() {
  const { data: documents = [], isLoading: docsLoading } = useQuery({
    queryKey: ["settings-knowledge-docs"],
    queryFn: () => listRagDocuments(),
  });

  if (docsLoading) return <SectionLoading />;

  return (
    <div className="p-6">
      <SectionHeader
        title="Knowledge"
        description="État du knowledge base Core et des documents RAG"
      />

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label="Documents RAG" value={documents.length} />
        <StatCard
          label="Chunks indexés"
          value={documents.reduce((acc, d) => acc + ((d as any).chunk_count ?? 0), 0)}
        />
        <StatCard label="Collections liées" value={new Set(documents.map((d) => (d as any).collection_id)).size} />
      </div>

      <WorkspaceLink href="/knowledge" label="Ouvrir le workspace Knowledge" />
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3">
      <p className="text-xs uppercase tracking-wider text-foreground-tertiary">{label}</p>
      <p className="mt-1 text-xl font-bold text-foreground">{value}</p>
    </div>
  );
}

/* ── RAG — editable engine configuration (/v1/rag/config) ───────── */

function RagSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data, isLoading } = useQuery({
    queryKey: ["settings-rag-config"],
    queryFn: () => getRagConfig(),
  });

  const [draft, setDraft] = React.useState<RagConfigResponse["config"] | null>(null);
  React.useEffect(() => {
    if (data?.config) setDraft({ ...data.config });
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: (cfg: RagConfigResponse["config"]) =>
      updateRagConfig({
        chunk_size: cfg.chunk_size,
        chunk_overlap: cfg.chunk_overlap,
        top_k: cfg.top_k,
        max_context_chars: cfg.max_context_chars,
        embedding_model: cfg.embedding_model ?? "",
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["settings-rag-config"] });
      addToast({ type: "success", message: "Configuration RAG enregistrée" });
      setDraft({ ...result.config });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec de la sauvegarde" }),
  });

  if (isLoading || !data || !draft) return <SectionLoading />;

  const dirty = JSON.stringify(draft) !== JSON.stringify(data.config);

  const numericFields: { key: keyof RagConfigResponse["config"]; label: string; min?: number }[] = [
    { key: "chunk_size", label: "Chunk size", min: 1 },
    { key: "chunk_overlap", label: "Chunk overlap", min: 0 },
    { key: "top_k", label: "Top K", min: 1 },
    { key: "max_context_chars", label: "Contexte max (caractères)", min: 100 },
  ];

  return (
    <div className="p-6">
      <SectionHeader
        title="RAG"
        description="Configuration du moteur d'ingestion et de récupération"
      />

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label="Documents" value={data.stats.documents} />
        <StatCard label="Chunks" value={data.stats.chunks} />
        <StatCard
          label="Embeddings"
          value={data.stats.embedding_mode === "llm" ? data.stats.embedding_model ?? "LLM" : "Fallback textuel"}
        />
      </div>

      <div className="max-w-xl space-y-3">
        {numericFields.map((f) => (
          <div key={String(f.key)} className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3">
            <span className="text-sm text-foreground-secondary">{f.label}</span>
            <Input
              type="number"
              className="w-40"
              min={f.min}
              value={String(draft[f.key] ?? "")}
              onChange={(e) => setDraft({ ...draft, [f.key]: Number(e.target.value) })}
            />
          </div>
        ))}
        <div className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3">
          <span className="text-sm text-foreground-secondary">
            Modèle d&apos;embedding
            <span className="block text-xs text-foreground-tertiary">Vide = fallback textuel</span>
          </span>
          <Input
            className="w-56 font-mono text-xs"
            placeholder="e.g. nomic-embed-text"
            value={draft.embedding_model ?? ""}
            onChange={(e) => setDraft({ ...draft, embedding_model: e.target.value || null })}
          />
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <Button
          variant="primary"
          onClick={() => saveMutation.mutate(draft)}
          disabled={!dirty || saveMutation.isPending}
        >
          {saveMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          <span className="ml-1">Enregistrer</span>
        </Button>
      </div>
    </div>
  );
}

/* ── Skills — live catalogue with real toggle (/v1/skills) ──────── */

function SkillsSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data: skills = [], isLoading } = useQuery({
    queryKey: ["settings-skills"],
    queryFn: () => listSkills(),
  });

  const toggleMutation = useMutation({
    mutationFn: (id: string) => toggleSkill(id),
    onSuccess: (skill) => {
      queryClient.invalidateQueries({ queryKey: ["settings-skills"] });
      addToast({ type: "success", message: `Skill « ${skill.name} » ${skill.is_active ? "activé" : "désactivé"}` });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec du toggle" }),
  });

  return (
    <div className="p-6">
      <SectionHeader
        title="Skills"
        description="Compétences enregistrées dans le Core"
      />

      {isLoading ? (
        <SectionLoading />
      ) : skills.length === 0 ? (
        <p className="text-sm text-foreground-tertiary">Aucune skill enregistrée.</p>
      ) : (
        <div className="space-y-2">
          {skills.map((s: Skill) => (
            <div
              key={s.id}
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <StatusDot ok={s.is_active} />
                  <span className="truncate text-sm font-medium text-foreground">{s.name}</span>
                  <span className="rounded-full bg-bg-2 px-2 py-0.5 text-[10px] text-foreground-tertiary">v{s.version}</span>
                </div>
                <p className="mt-0.5 truncate text-xs text-foreground-tertiary">{s.description}</p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => toggleMutation.mutate(s.id)}
                disabled={toggleMutation.isPending}
                aria-label={`Toggle ${s.name}`}
              >
                {toggleMutation.isPending && toggleMutation.variables === s.id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : s.is_active ? (
                  <ToggleRight className="h-5 w-5" />
                ) : (
                  <ToggleLeft className="h-5 w-5 text-foreground-tertiary" />
                )}
              </Button>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6">
        <WorkspaceLink href="/skills/lab" label="Ouvrir le Skills Lab" />
      </div>
    </div>
  );
}

/* ── Agents — live state + workspace link ───────────────────────── */

function AgentsSection() {
  const { data: agents = [], isLoading } = useQuery({
    queryKey: ["settings-agents"],
    queryFn: () => listAgents(),
  });

  if (isLoading) return <SectionLoading />;

  return (
    <div className="p-6">
      <SectionHeader
        title="Agents"
        description="État des agents enregistrés dans le Runtime"
      />

      {agents.length === 0 ? (
        <p className="text-sm text-foreground-tertiary">Aucun agent enregistré.</p>
      ) : (
        <div className="space-y-2">
          {agents.map((a) => (
            <div
              key={a.id}
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <StatusDot ok={a.status === "running" || a.status === "idle"} />
                  <span className="truncate text-sm font-medium text-foreground">{a.name}</span>
                </div>
                <p className="mt-0.5 truncate text-xs text-foreground-tertiary">
                  {a.status} · {a.capabilities.join(", ") || "aucune capacité"}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6">
        <WorkspaceLink href="/agents" label="Ouvrir le workspace Agents" />
      </div>
    </div>
  );
}

/* ── Tools — live Core tool catalogue (/v1/tools) ───────────────── */

function ToolsCatalogueSection() {
  const { data: tools = [], isLoading } = useQuery({
    queryKey: ["settings-tools"],
    queryFn: () => listTools(),
  });

  if (isLoading) return <SectionLoading />;

  return (
    <div className="p-6">
      <SectionHeader
        title="Tools"
        description="Catalogue d'outils du Core (builtin, custom, MCP)"
      />

      {tools.length === 0 ? (
        <p className="text-sm text-foreground-tertiary">Aucun outil dans le catalogue.</p>
      ) : (
        <div className="space-y-2">
          {tools.map((t: CoreTool) => (
            <div
              key={t.id}
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <StatusDot ok={t.is_available} />
                  <span className="truncate text-sm font-medium text-foreground">{t.name}</span>
                  <span className="rounded-full bg-bg-2 px-2 py-0.5 text-[10px] uppercase text-foreground-tertiary">
                    {t.provider}
                  </span>
                </div>
                <p className="mt-0.5 truncate text-xs text-foreground-tertiary">{t.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6">
        <WorkspaceLink href="/tools" label="Ouvrir le workspace Tools" />
      </div>
    </div>
  );
}

/* ── MCP — full server management (/v1/tools/servers) ───────────── */

function McpServersSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [registerOpen, setRegisterOpen] = React.useState(false);
  const [newServer, setNewServer] = React.useState({ name: "", url: "", description: "" });

  const { data: servers = [], isLoading } = useQuery({
    queryKey: ["settings-mcp-servers"],
    queryFn: () => listToolServers(),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["settings-mcp-servers"] });

  const registerMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => registerToolServer(data),
    onSuccess: (srv) => {
      invalidate();
      addToast({ type: "success", message: `Serveur MCP « ${srv.name} » enregistré` });
      setRegisterOpen(false);
      setNewServer({ name: "", url: "", description: "" });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec de l'enregistrement" }),
  });

  const toggleMutation = useMutation({
    mutationFn: (srv: ToolServer) => updateToolServer(srv.id, { enabled: !srv.enabled }),
    onSuccess: () => {
      invalidate();
      addToast({ type: "success", message: "Serveur MCP mis à jour" });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec de la mise à jour" }),
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => setToolServerStatus(id, status),
    onSuccess: (srv) => {
      invalidate();
      addToast({
        type: srv.status === "error" ? "error" : "success",
        message: `Statut du serveur « ${srv.name} » : ${srv.status}`,
      });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec du test de connexion" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteToolServer(id),
    onSuccess: () => {
      invalidate();
      addToast({ type: "success", message: "Serveur MCP supprimé" });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec de la suppression" }),
  });

  return (
    <div className="p-6">
      <SectionHeader title="MCP" description="Serveurs MCP connectés au Core" />

      <div className="mb-4 flex items-center justify-between gap-4">
        <span className="text-sm text-foreground-tertiary">{servers.length} serveur(s)</span>
        <Button size="sm" variant="primary" onClick={() => setRegisterOpen(true)}>
          <Plus className="h-3.5 w-3.5" />
          <span className="ml-1">Ajouter un serveur</span>
        </Button>
      </div>

      {isLoading ? (
        <SectionLoading />
      ) : servers.length === 0 ? (
        <p className="text-sm text-foreground-tertiary">Aucun serveur MCP enregistré.</p>
      ) : (
        <div className="space-y-2">
          {servers.map((srv: ToolServer) => (
            <McpServerRow
              key={srv.id}
              server={srv}
              onToggle={() => toggleMutation.mutate(srv)}
              onCheck={() => statusMutation.mutate({ id: srv.id, status: "checking" })}
              onDelete={() => deleteMutation.mutate(srv.id)}
              busy={toggleMutation.isPending || deleteMutation.isPending}
              busyId={String(toggleMutation.variables?.id ?? deleteMutation.variables ?? "")}
            />
          ))}
        </div>
      )}

      {/* Register dialog */}
      <Dialog open={registerOpen} onOpenChange={setRegisterOpen} title="Nouveau serveur MCP">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Nom</label>
            <Input value={newServer.name} onChange={(e) => setNewServer({ ...newServer, name: e.target.value })} placeholder="e.g. filesystem" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">URL</label>
            <Input value={newServer.url} onChange={(e) => setNewServer({ ...newServer, url: e.target.value })} placeholder="e.g. http://localhost:8080/mcp" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Description</label>
            <Input value={newServer.description} onChange={(e) => setNewServer({ ...newServer, description: e.target.value })} placeholder="Optionnelle" />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setRegisterOpen(false)}>Annuler</Button>
            <Button
              variant="primary"
              disabled={!newServer.name || !newServer.url || registerMutation.isPending}
              onClick={() => registerMutation.mutate(newServer)}
            >
              {registerMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
              <span className="ml-1">Enregistrer</span>
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

function McpServerRow({
  server,
  onToggle,
  onCheck,
  onDelete,
  busy,
  busyId,
}: {
  server: ToolServer;
  onToggle: () => void;
  onCheck: () => void;
  onDelete: () => void;
  busy: boolean;
  busyId: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <StatusDot ok={server.enabled && server.status !== "error"} />
          <span className="truncate text-sm font-medium text-foreground">{server.name}</span>
          {server.status && (
            <span className="rounded-full bg-bg-2 px-2 py-0.5 text-[10px] uppercase text-foreground-tertiary">
              {server.status}
            </span>
          )}
        </div>
        {server.url && (
          <p className="mt-0.5 truncate font-mono text-xs text-foreground-tertiary">{server.url}</p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-1">
        <Button size="sm" variant="ghost" onClick={onCheck} disabled={busy} aria-label={`Tester ${server.name}`}>
          {busy && busyId === server.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
        </Button>
        <Button size="sm" variant="ghost" onClick={onToggle} disabled={busy} aria-label={`Toggle ${server.name}`}>
          {busy && busyId === server.id ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : server.enabled ? (
            <ToggleRight className="h-5 w-5" />
          ) : (
            <ToggleLeft className="h-5 w-5 text-foreground-tertiary" />
          )}
        </Button>
        <Button size="sm" variant="ghost" onClick={onDelete} disabled={busy} aria-label={`Supprimer ${server.name}`}>
          {busy && busyId === server.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
        </Button>
      </div>
    </div>
  );
}

/* ── Providers — full CRUD on real providers (/providers) ───────── */

function ProvidersSection({
  selectedProviderId,
  onSelect,
}: {
  selectedProviderId: string | null;
  onSelect: (id: string | null) => void;
}) {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [search, setSearch] = React.useState("");

  const [addOpen, setAddOpen] = React.useState(false);
  const [editOpen, setEditOpen] = React.useState(false);
  const [newProvider, setNewProvider] = React.useState<Partial<ProviderCreate>>({});
  const [editProvider, setEditProvider] = React.useState<Provider | null>(null);
  const [testingId, setTestingId] = React.useState<string | null>(null);

  const { data: providers = [], isLoading } = useQuery({
    queryKey: ["providers"],
    queryFn: () => listProviders(),
  });

  const selectedProvider = providers.find((p) => p.id === selectedProviderId) || null;
  const filteredProviders = providers.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      ((p as any).display_name || "").toLowerCase().includes(search.toLowerCase()),
  );

  const createMutation = useMutation({
    mutationFn: (data: ProviderCreate) => createProvider(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider créé" });
    },
    onError: (err) => addToast({ type: "error", message: err instanceof Error ? err.message : "Échec création" }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProviderUpdate }) => updateProvider(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider mis à jour" });
    },
    onError: (err) => addToast({ type: "error", message: err instanceof Error ? err.message : "Échec mise à jour" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider supprimé" });
    },
    onError: (err) => addToast({ type: "error", message: err instanceof Error ? err.message : "Échec suppression" }),
  });

  const defaultMutation = useMutation({
    mutationFn: (id: string) => setDefaultProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider défini comme défaut" });
    },
    onError: (err) => addToast({ type: "error", message: err instanceof Error ? err.message : "Échec" }),
  });

  const handleToggle = (p: Provider) =>
    updateMutation.mutate({ id: p.id, data: { enabled: !p.enabled } });

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const result = await testProviderConnection(id);
      addToast({
        type: result.connected ? "success" : "error",
        message: result.message || (result.connected ? "Connexion OK" : "Connexion échouée"),
      });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Test échoué" });
    } finally {
      setTestingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
    if (selectedProviderId === id) onSelect(null);
  };

  return (
    <div className="flex h-full min-h-0">
      {/* Provider list */}
      <div className="flex w-80 shrink-0 flex-col border-r border-line-1">
        <div className="flex items-center justify-between gap-2 px-4 py-3">
          <Input placeholder="Rechercher…" value={search} onChange={(e) => setSearch(e.target.value)} />
          <Button size="sm" variant="primary" onClick={() => setAddOpen(true)} aria-label="Ajouter un provider">
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </div>
        <div className="custom-scrollbar flex-1 overflow-y-auto" style={{ padding: "8px" }}>
          {isLoading ? (
            <SectionLoading />
          ) : filteredProviders.length === 0 ? (
            <p className="px-2 py-4 text-sm text-foreground-tertiary">Aucun provider.</p>
          ) : (
            filteredProviders.map((p) => (
              <button
                key={p.id}
                onClick={() => onSelect(p.id)}
                className={cn("list-item w-full", selectedProviderId === p.id && "active")}
                style={{ width: "100%", border: "none", background: "transparent", textAlign: "left" }}
              >
                <StatusDot ok={p.enabled && p.status !== "disconnected"} />
                <span className="min-w-0 flex-1 truncate">{p.name}</span>
                {p.is_default && (
                  <span className="rounded-full bg-accent/10 px-1.5 py-0.5 text-[10px] uppercase text-accent">default</span>
                )}
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => { e.stopPropagation(); handleToggle(p); }}
                  onKeyDown={(e) => { if (e.key === "Enter") { e.stopPropagation(); handleToggle(p); } }}
                  aria-label={`Toggle ${p.name}`}
                  className="shrink-0 text-accent"
                >
                  {p.enabled ? <ToggleRight className="h-4 w-4" /> : <ToggleLeft className="h-4 w-4" />}
                </span>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Provider detail */}
      <div className="custom-scrollbar flex-1 overflow-y-auto p-6">
        {!selectedProvider ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <Database className="mb-3 h-10 w-10 text-foreground-tertiary" />
            <p className="text-sm text-muted-foreground">Sélectionnez un provider pour le configurer.</p>
          </div>
        ) : (
          <ProviderDetail
            provider={selectedProvider}
            onTest={() => handleTest(selectedProvider.id)}
            onEdit={() => { setEditProvider(selectedProvider); setEditOpen(true); }}
            onSetDefault={() => defaultMutation.mutate(selectedProvider.id)}
            onDelete={() => handleDelete(selectedProvider.id)}
            testing={testingId === selectedProvider.id}
            defaulting={defaultMutation.isPending && defaultMutation.variables === selectedProvider.id}
            deleting={deleteMutation.isPending && deleteMutation.variables === selectedProvider.id}
          />
        )}
      </div>

      {/* Add provider dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen} title="Nouveau provider">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Nom</label>
            <Input value={newProvider.name || ""} onChange={(e) => setNewProvider({ ...newProvider, name: e.target.value })} placeholder="e.g. Ollama" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Type</label>
            <Input value={newProvider.type || ""} onChange={(e) => setNewProvider({ ...newProvider, type: e.target.value })} placeholder="e.g. ollama" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">URL de base</label>
            <Input value={newProvider.base_url || ""} onChange={(e) => setNewProvider({ ...newProvider, base_url: e.target.value })} placeholder="e.g. http://localhost:11434" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Modèle par défaut</label>
            <Input value={newProvider.default_model || ""} onChange={(e) => setNewProvider({ ...newProvider, default_model: e.target.value })} placeholder="e.g. qwen2.5-coder" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Clé API</label>
            <Input type="password" value={newProvider.api_key || ""} onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })} placeholder="Optionnelle" />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setAddOpen(false)}>Annuler</Button>
            <Button
              variant="primary"
              disabled={!newProvider.name || !newProvider.type || createMutation.isPending}
              onClick={async () => {
                await createMutation.mutateAsync(newProvider as ProviderCreate);
                setNewProvider({});
                setAddOpen(false);
              }}
            >
              {createMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
              <span className="ml-1">Créer</span>
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Edit provider dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen} title="Configurer le provider">
        {editProvider && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">URL de base</label>
              <Input value={editProvider.base_url || ""} onChange={(e) => setEditProvider({ ...editProvider, base_url: e.target.value })} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Modèle par défaut</label>
              <Input value={editProvider.default_model || ""} onChange={(e) => setEditProvider({ ...editProvider, default_model: e.target.value })} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Clé API</label>
              <Input type="password" value={(editProvider as any).api_key || ""} onChange={(e) => setEditProvider({ ...editProvider, api_key: e.target.value } as any)} placeholder="Laisser vide pour conserver" />
            </div>
            <label className="flex items-center gap-2 text-sm text-foreground-secondary">
              <input
                type="checkbox"
                checked={editProvider.enabled}
                onChange={(e) => setEditProvider({ ...editProvider, enabled: e.target.checked })}
                className="accent-accent"
              />
              Actif
            </label>
            <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
              <Button variant="ghost" onClick={() => { setEditOpen(false); setEditProvider(null); }}>Annuler</Button>
              <Button
                variant="primary"
                disabled={updateMutation.isPending}
                onClick={async () => {
                  await updateMutation.mutateAsync({
                    id: editProvider.id,
                    data: {
                      base_url: editProvider.base_url,
                      default_model: editProvider.default_model,
                      display_name: (editProvider as any).display_name,
                      enabled: editProvider.enabled,
                    },
                  });
                  setEditOpen(false);
                  setEditProvider(null);
                }}
              >
                {updateMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                <span className="ml-1">Enregistrer</span>
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}

function ProviderDetail({
  provider,
  onTest,
  onEdit,
  onSetDefault,
  onDelete,
  testing,
  defaulting,
  deleting,
}: {
  provider: Provider;
  onTest: () => void;
  onEdit: () => void;
  onSetDefault: () => void;
  onDelete: () => void;
  testing: boolean;
  defaulting: boolean;
  deleting: boolean;
}) {
  return (
    <div>
      <SectionHeader
        title={provider.name}
        description={`${provider.type} · ${provider.status}`}
      />
      <div className="max-w-xl space-y-3">
        <InfoRow label="URL de base" value={provider.base_url || "—"} />
        <InfoRow label="Modèle par défaut" value={provider.default_model || "—"} />
        <InfoRow label="Défaut système" value={provider.is_default ? "Oui" : "Non"} />
        {provider.models.length > 0 && (
          <div className="rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3">
            <p className="mb-2 text-xs uppercase tracking-wider text-foreground-tertiary">Modèles</p>
            <div className="flex flex-wrap gap-1.5">
              {provider.models.map((model) => (
                <span key={model} className="rounded-full bg-bg-2 px-2.5 py-0.5 text-xs text-foreground-secondary">
                  {model}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 flex max-w-xl flex-wrap gap-2">
        <Button size="sm" variant="secondary" onClick={onTest} disabled={testing}>
          {testing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
          <span className="ml-1">Tester la connexion</span>
        </Button>
        <Button size="sm" variant="secondary" onClick={onEdit}>
          <Edit3 className="h-3.5 w-3.5" />
          <span className="ml-1">Configurer</span>
        </Button>
        <Button size="sm" variant="secondary" onClick={onSetDefault} disabled={defaulting}>
          {defaulting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          <span className="ml-1">Définir comme défaut</span>
        </Button>
        <Button size="sm" variant="destructive" onClick={onDelete} disabled={deleting}>
          {deleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
          <span className="ml-1">Supprimer</span>
        </Button>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3">
      <span className="text-xs uppercase tracking-wider text-foreground-tertiary">{label}</span>
      <span className="truncate font-mono text-sm text-foreground-secondary">{value}</span>
    </div>
  );
}













