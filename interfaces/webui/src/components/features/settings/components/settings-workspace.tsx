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
  type Provider,
} from "@/lib/api/providers";
import { listModels, toggleModel, type ModelInfo } from "@/lib/api/models";
import {
  getRagConfig,
  getRagStrategies,
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
import {
  listIntegrations,
  type Integration,
  type IntegrationKind,
} from "@/lib/api/integrations";
import {
  ChatSection,
  SearchSection,
  RemindersSection,
  ShortcutsSection,
  LibrarySection,
  SystemSection,
  SecuritySection,
} from "./settings-sections";
import { CapabilitiesSection } from "./capabilities-section";

import {
  ChunkingSection,
  EmbeddingsSection,
  ModelRoutersSection,
  RerankingSection,
  SpeechToTextSection,
  VectorDatabaseSection,
} from "./settings-ai-sections";
import { useUIStore } from "@/store/ui.store";
import { useTheme } from "@/providers/theme-provider";
import {
  ACCENT_PRESETS,
  setStoredAccent,
  getActiveAccentId,
} from "@/lib/accent";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { capabilityLabel, capabilityVariant } from "@/lib/llm/capabilities";
import {
  AudioLines,
  Braces,
  Palette,
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
  Loader2,
  ExternalLink,
  ToggleLeft,
  ToggleRight,
  Save,
  MessageSquare,
  Search,
  Bell,
  Keyboard,
  FolderOpen,
  Shield,
  SlidersHorizontal,
  AlertCircle,
  Lock,
  Globe,
  Clock,
  Puzzle,
  Layers,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Package,
  Settings2,
  RotateCcw,
} from "lucide-react";

import { SETTINGS_GROUPS, type SettingsSectionId } from "../settings-nav";

type Section = SettingsSectionId;

/** Sections (libellés + icônes) — ids pilotés par `settings-nav` (testé). */
export const SECTIONS: {
  id: Section;
  label: string;
  icon: React.ReactNode;
  category: "system" | "user" | "project" | "conversation";
}[] = [
  // Groupe « General » — chaque entrée est une capacité/état réel.
  { id: "chat", label: "Chat", icon: <MessageSquare className="h-4 w-4" />, category: "conversation" },
  { id: "providers", label: "Providers", icon: <Layers className="h-4 w-4" />, category: "system" },
  { id: "models", label: "Models", icon: <Bot className="h-4 w-4" />, category: "system" },
  { id: "routers", label: "Model Routers", icon: <Network className="h-4 w-4" />, category: "system" },
  { id: "appearance", label: "Appearance", icon: <Palette className="h-4 w-4" />, category: "user" },
  { id: "knowledge", label: "Knowledge", icon: <BookOpen className="h-4 w-4" />, category: "system" },
  { id: "rag", label: "RAG", icon: <Database className="h-4 w-4" />, category: "system" },
  { id: "embedding", label: "Embeddings", icon: <Sparkles className="h-4 w-4" />, category: "system" },
  { id: "vector-db", label: "Vector Database", icon: <Database className="h-4 w-4" />, category: "system" },
  { id: "chunking", label: "Text Splitting & Chunking", icon: <Braces className="h-4 w-4" />, category: "system" },
  { id: "reranking", label: "Retrieval & Reranking", icon: <Zap className="h-4 w-4" />, category: "system" },
  { id: "speech", label: "Speech-to-Text", icon: <AudioLines className="h-4 w-4" />, category: "system" },
  { id: "skills", label: "Skills", icon: <Wrench className="h-4 w-4" />, category: "system" },
  { id: "search", label: "Search", icon: <Search className="h-4 w-4" />, category: "system" },
  { id: "integrations", label: "Integrations", icon: <Network className="h-4 w-4" />, category: "system" },
  { id: "reminders", label: "Reminders", icon: <Bell className="h-4 w-4" />, category: "user" },
  { id: "shortcuts", label: "Shortcuts", icon: <Keyboard className="h-4 w-4" />, category: "user" },
  { id: "capabilities", label: "Capabilities", icon: <Puzzle className="h-4 w-4" />, category: "system" },
  { id: "library", label: "Library", icon: <FolderOpen className="h-4 w-4" />, category: "project" },
  { id: "system", label: "System", icon: <SlidersHorizontal className="h-4 w-4" />, category: "system" },
  { id: "security", label: "Security", icon: <Shield className="h-4 w-4" />, category: "system" },
];

export function SettingsWorkspace() {
  const [activeSection, setActiveSection] = React.useState<Section>("chat");
  const [search, setSearch] = React.useState("");

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

  // Recherche de section — présentation seule (filtre les libellés de la
  // taxinomie `settings-nav`). Aucun état métier : la vérité reste dans Core.
  const query = search.trim().toLowerCase();
  const filteredGroups = React.useMemo(
    () =>
      SETTINGS_GROUPS.map((group) => ({
        ...group,
        items: group.items.filter((id) => {
          const section = SECTIONS.find((s) => s.id === id);
          return section ? section.label.toLowerCase().includes(query) : false;
        }),
      })).filter((group) => group.items.length > 0),
    [query],
  );

  return (
    <div className="flex h-full min-h-0">
      {/* Left panel: section navigation */}
      <div className="flex w-64 shrink-0 flex-col border-r border-line-1" style={{ background: "var(--panel)" }}>
        <div className="border-b border-line-1 px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground">Settings</h2>
        </div>
        {/* Filtre de sections (24 entrées → navigation guidée), fixe au-dessus
            de la liste : il ne défile pas avec les sections. */}
        <div className="border-b border-line-1 px-3 py-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-foreground-tertiary" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher une section…"
              aria-label="Rechercher une section Settings"
              className="pl-7"
            />
          </div>
        </div>
        <nav className="sidebar-inner custom-scrollbar" style={{ padding: "8px" }}>
          {/* Navigation groupée (arborescence cible, taxonomie : settings-nav). */}
          {filteredGroups.length === 0 ? (
            <p className="px-2 py-3 text-xs text-muted-foreground">
              Aucune section ne correspond à « {search.trim()} ».
            </p>
          ) : (
            filteredGroups.map((group) => {
              const sections = group.items
                .map((id) => SECTIONS.find((s) => s.id === id))
                .filter((s): s is (typeof SECTIONS)[number] => s !== undefined);
              // Groupe à section unique rendu sans en-tête (pas de « Skills ›
              // Skills ») — sauf pendant une recherche, où l'en-tête situe le
              // résultat dans l'arborescence (toujours sans doublon de libellé).
              const showHeader =
                sections.length > 1 ||
                (query.length > 0 &&
                  sections.every((s) => s.label.toLowerCase() !== group.label.toLowerCase()));
              return (
                <div key={group.id} className="mb-1.5">
                  {showHeader && (
                    <div className="px-2 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wide text-foreground-tertiary">
                      {group.label}
                    </div>
                  )}
                  {sections.map((section) => (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={cn("list-item w-full", activeSection === section.id && "active")}
                      style={{
                        width: "100%",
                        border: "none",
                        background: "transparent",
                        textAlign: "left",
                      }}
                    >
                      {section.icon}
                      <span>{section.label}</span>
                    </button>
                  ))}
                </div>
              );
            })
          )}
        </nav>
      </div>

      {/* Right panel: section content */}
      <div className="flex-1 min-w-0 overflow-y-auto" data-testid="settings-section-content">
        {activeSection === "chat" && <ChatSection />}
        {activeSection === "appearance" && <AppearanceSection />}
        {activeSection === "knowledge" && <KnowledgeSection />}
        {activeSection === "rag" && <RagSection />}
        {activeSection === "embedding" && <EmbeddingsSection />}
        {activeSection === "vector-db" && <VectorDatabaseSection />}
        {activeSection === "chunking" && <ChunkingSection />}
        {activeSection === "reranking" && <RerankingSection />}
        {activeSection === "speech" && <SpeechToTextSection />}
        {activeSection === "routers" && <ModelRoutersSection />}
        {activeSection === "providers" && <ProvidersSection />}
        {activeSection === "models" && <ModelsSection />}
        {activeSection === "skills" && <SkillsSection />}
        {activeSection === "search" && <SearchSection />}
        {activeSection === "integrations" && <IntegrationsSection />}
        {activeSection === "reminders" && <RemindersSection />}
        {activeSection === "shortcuts" && <ShortcutsSection />}
        {activeSection === "capabilities" && <CapabilitiesSection />}
        {activeSection === "library" && <LibrarySection />}
        {activeSection === "system" && <SystemSection />}
        {activeSection === "security" && <SecuritySection />}
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
      <div className="flex max-w-xl items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
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
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3"
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

      <div className="flex flex-wrap items-center gap-2">
        <WorkspaceLink href="/knowledge" label="Ouvrir le workspace Knowledge" />
        <WorkspaceLink href="#rag" label="Configurer le moteur RAG" />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
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

  // Stratégies réellement implémentées dans le Core (aucune inventée côté UI).
  const { data: strategiesData } = useQuery({
    queryKey: ["rag-strategies"],
    queryFn: () => getRagStrategies(),
    staleTime: 300_000,
  });
  const strategies = strategiesData?.strategies ?? [];

  const saveMutation = useMutation({
    mutationFn: (cfg: RagConfigResponse["config"]) =>
      updateRagConfig({
        chunk_size: cfg.chunk_size,
        chunk_overlap: cfg.chunk_overlap,
        top_k: cfg.top_k,
        max_context_chars: cfg.max_context_chars,
        embedding_model: cfg.embedding_model ?? "",
        strategy: cfg.strategy,
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
          <div key={String(f.key)} className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
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
        <div className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
          <span className="text-sm text-foreground-secondary">
            Stratégie de recherche
            <span className="block text-xs text-foreground-tertiary">
              {strategies.find((s) => s.id === draft.strategy)?.description ??
                "Comportement par défaut du moteur RAG (surchargeable par collection)."}
            </span>
          </span>
          <select
            className="w-56 shrink-0 rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 text-sm text-foreground"
            value={draft.strategy}
            onChange={(e) => setDraft({ ...draft, strategy: e.target.value })}
          >
            {strategies.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
        {data.stats.recommendation && (
          <p className="rounded-lg border border-line-1 bg-bg-1 px-4 py-2.5 text-xs text-foreground-secondary">
            <span className="font-medium text-foreground">Recommandation ETHAN : </span>
            {strategies.find((s) => s.id === data.stats.recommendation?.strategy_id)?.label ??
              data.stats.recommendation.strategy_id}
            {" — "}
            {data.stats.recommendation.reason}
          </p>
        )}
        <div className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
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
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3"
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
        {/* Lien réel uniquement : la route /skills/lab n'existe pas dans la
            WebUI (le Skills Lab côté Core reste servi par l'API /v1/skills/lab)
            — on pointe le workspace Skills existant (règle anti-fantôme). */}
        <WorkspaceLink href="/skills" label="Ouvrir le workspace Skills" />
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
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3"
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

/* ── Integrations — external service connections (/v1/integrations)  */

function IntegrationsSection() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [showCreate, setShowCreate] = React.useState(false);

  const { data: integrations = [], isLoading } = useQuery({
    queryKey: ["settings-integrations"],
    queryFn: () => listIntegrations(),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["settings-integrations"] });
  };

  const connectMutation = useMutation({
    mutationFn: (id: string) =>
      import("@/lib/api/integrations").then((m) => m.connectIntegration(id)),
    onSuccess: invalidate,
  });

  const disconnectMutation = useMutation({
    mutationFn: (id: string) =>
      import("@/lib/api/integrations").then((m) => m.disconnectIntegration(id)),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      import("@/lib/api/integrations").then((m) => m.deleteIntegration(id)),
    onSuccess: () => {
      invalidate();
      setSelectedId(null);
    },
  });

  if (isLoading) return <SectionLoading />;

  const selected = integrations.find((i) => i.id === selectedId) ?? null;

  return (
    <div className="flex h-full min-h-0">
      <div className="flex w-80 shrink-0 flex-col border-r border-line-1">
        <div className="flex items-center justify-between border-b border-line-1 px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground">Integrations</h2>
          <Button size="sm" onClick={() => setShowCreate(true)}>
            <Plus className="mr-1 h-3 w-3" /> Add
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {integrations.length === 0 ? (
            <p className="px-2 py-8 text-center text-sm text-muted-foreground">
              No integrations configured.
            </p>
          ) : (
            integrations.map((integration) => (
              <button
                key={integration.id}
                onClick={() => setSelectedId(integration.id)}
                className={cn(
                  "mb-1 w-full rounded-md px-3 py-2 text-left transition-colors",
                  selectedId === integration.id
                    ? "bg-[var(--accent)]/10 text-foreground"
                    : "hover:bg-[var(--panel-hover)] text-foreground-secondary",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium truncate">{integration.name}</span>
                  <StatusDot ok={integration.status === "connected"} />
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground capitalize">
                  {integration.kind.replace(/-/g, " ")}
                </div>
              </button>
            ))
          )}
        </div>
      </div>
      <div className="flex-1 min-w-0 overflow-y-auto p-6">
        {showCreate ? (
          <IntegrationCreateForm
            onCancel={() => setShowCreate(false)}
            onSuccess={() => {
              setShowCreate(false);
              invalidate();
            }}
          />
        ) : selected ? (
          <IntegrationDetail
            integration={selected}
            onConnect={() => connectMutation.mutate(selected.id)}
            onDisconnect={() => disconnectMutation.mutate(selected.id)}
            onDelete={() => deleteMutation.mutate(selected.id)}
            isConnecting={connectMutation.isPending || disconnectMutation.isPending}
            isDeleting={deleteMutation.isPending}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            Select an integration or create a new one.
          </div>
        )}
      </div>
    </div>
  );
}

function IntegrationDetail({
  integration,
  onConnect,
  onDisconnect,
  onDelete,
  isConnecting,
  isDeleting,
}: {
  integration: Integration;
  onConnect: () => void;
  onDisconnect: () => void;
  onDelete: () => void;
  isConnecting: boolean;
  isDeleting: boolean;
}) {
  const statusColor =
    integration.status === "connected"
      ? "text-[var(--green)]"
      : integration.status === "error"
        ? "text-[var(--red)]"
        : "text-muted-foreground";

  return (
    <div>
      <SectionHeader
        title={integration.name}
        description={integration.description || `${integration.kind} integration`}
      />
      <div className="mb-6 grid gap-4">
        <div className="rounded-lg border border-line-1 p-4">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Status</h3>
          <div className="flex items-center gap-2">
            <StatusDot ok={integration.status === "connected"} />
            <span className={cn("text-sm font-medium capitalize", statusColor)}>
              {integration.status}
            </span>
            {integration.last_connected_at && (
              <span className="ml-auto text-xs text-muted-foreground">
                Last: {new Date(integration.last_connected_at).toLocaleString()}
              </span>
            )}
          </div>
          <div className="mt-3 flex gap-2">
            {integration.status === "connected" ? (
              <Button size="sm" variant="outline" onClick={onDisconnect} disabled={isConnecting}>
                {isConnecting ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : null}
                Disconnect
              </Button>
            ) : (
              <Button size="sm" onClick={onConnect} disabled={isConnecting}>
                {isConnecting ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <Play className="mr-1 h-3 w-3" />}
                Connect
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={onDelete} disabled={isDeleting}>
              {isDeleting ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <Trash2 className="mr-1 h-3 w-3" />}
              Remove
            </Button>
          </div>
        </div>
        <div className="rounded-lg border border-line-1 p-4">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Configuration</h3>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Kind</dt>
              <dd className="capitalize">{integration.kind.replace(/-/g, " ")}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Enabled</dt>
              <dd>{integration.enabled ? "Yes" : "No"}</dd>
            </div>
            {Object.entries(integration.config).map(([key, value]) => (
              <div key={key}>
                <dt className="text-muted-foreground">{key}</dt>
                <dd className="truncate font-mono text-xs">
                  {typeof value === "object" ? JSON.stringify(value) : String(value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
        {integration.credential_keys.length > 0 && (
          <div className="rounded-lg border border-line-1 p-4">
            <h3 className="mb-3 text-sm font-semibold text-foreground">Credentials</h3>
            <p className="text-xs text-muted-foreground mb-2">
              Stored securely in Core. Only key names are shown.
            </p>
            <div className="flex flex-wrap gap-2">
              {integration.credential_keys.map((key) => (
                <span key={key} className="rounded-full bg-[var(--panel)] px-2 py-0.5 text-xs font-mono text-foreground-secondary">
                  {key}
                </span>
              ))}
            </div>
          </div>
        )}
        {integration.capabilities.length > 0 && (
          <div className="rounded-lg border border-line-1 p-4">
            <h3 className="mb-3 text-sm font-semibold text-foreground">Capabilities</h3>
            <div className="flex flex-wrap gap-2">
              {integration.capabilities.map((cap) => (
                <span key={cap} className="rounded-full bg-[var(--accent)]/10 px-2 py-0.5 text-xs text-[var(--accent)]">
                  {cap}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function IntegrationCreateForm({
  onCancel,
  onSuccess,
}: {
  onCancel: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = React.useState("");
  const [kind, setKind] = React.useState<IntegrationKind>("mcp");
  const [description, setDescription] = React.useState("");
  const [configText, setConfigText] = React.useState("{}");

  const createMutation = useMutation({
    mutationFn: (data: {
      name: string;
      kind: IntegrationKind;
      description: string;
      config: Record<string, unknown>;
    }) => import("@/lib/api/integrations").then((m) => m.createIntegration(data)),
    onSuccess,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let config: Record<string, unknown> = {};
    try {
      config = JSON.parse(configText || "{}");
    } catch {
      return;
    }
    createMutation.mutate({ name, kind, description, config });
  };

  return (
    <form onSubmit={handleSubmit}>
      <SectionHeader title="New Integration" description="Register a new external service connection." />
      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Name</label>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Kind</label>
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as IntegrationKind)}
            className="w-full rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 text-sm text-foreground"
          >
            <option value="mcp">MCP</option>
            <option value="web-search">Web Search</option>
            <option value="storage">Storage</option>
            <option value="automation">Automation</option>
            <option value="developer">Developer</option>
            <option value="external-app">External App</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Description</label>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Config (JSON)</label>
          <textarea
            value={configText}
            onChange={(e) => setConfigText(e.target.value)}
            rows={4}
            className="w-full rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 font-mono text-xs text-foreground"
          />
        </div>
      </div>
      <div className="mt-6 flex gap-2">
        <Button type="submit" disabled={createMutation.isPending || !name.trim()}>
          {createMutation.isPending ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <Plus className="mr-1 h-3 w-3" />}
          Create
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
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
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3"
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
    <div className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
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

/* ── Providers — live Core state + workspace link ───────────────── */

/**
 * Vue « Providers » des Settings : état live issu de GET /providers et
 * navigation vers le workspace dédié /providers.
 *
 * La gestion complète (création, endpoint, authentification, activation,
 * test de connexion, découverte des modèles, modèle par défaut, moteur par
 * défaut) vit exclusivement dans le workspace Providers : cette section n'en
 * duplique aucune (règle AGENTS.md — l'interface révèle, elle ne redéfinit
 * pas). Les capacités affichées sont celles déclarées par le Core
 * (`provider.capabilities`) : elles ne sont jamais déduites du type.
 */
function ProvidersSection() {
  const { data: providers = [], isLoading } = useQuery({
    queryKey: ["providers"],
    queryFn: () => listProviders(),
  });

  const connected = providers.filter((p) => p.status === "connected").length;
  const enabled = providers.filter((p) => p.enabled).length;
  const defaultProvider = providers.find((p) => p.is_default) ?? null;

  return (
    <div className="p-6">
      <SectionHeader
        title="Providers"
        description="Fournisseurs réellement configurés dans le Core — état en temps réel"
      />

      <div className="mb-4">
        <WorkspaceLink href="/providers" label="Ouvrir le workspace Providers" />
      </div>

      {isLoading ? (
        <SectionLoading />
      ) : providers.length === 0 ? (
        <p className="text-sm text-foreground-tertiary">
          Aucun provider configuré. Ajoutez-le depuis le workspace Providers.
        </p>
      ) : (
        <>
          <div className="mb-4 grid grid-cols-3 gap-3">
            <StatCard label="Configurés" value={providers.length} />
            <StatCard label="Actifs" value={enabled} />
            <StatCard label="Connectés" value={connected} />
          </div>
          <div className="space-y-2">
            {providers.map((p: Provider) => (
              <div
                key={p.id}
                className="rounded-lg border border-line-1 bg-bg-1 px-4 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-2">
                    <StatusDot ok={p.status === "connected"} />
                    <span className="truncate text-sm font-medium text-foreground">{p.name}</span>
                    <span className="text-xs uppercase text-foreground-tertiary">{p.type}</span>
                    {p.is_default && (
                      <Badge variant="solid" size="sm">
                        moteur par défaut
                      </Badge>
                    )}
                    {!p.enabled && (
                      <Badge variant="dim" size="sm">
                        inactif
                      </Badge>
                    )}
                  </div>
                  {p.default_model && (
                    <span className="shrink-0 font-mono text-xs text-foreground-tertiary">
                      {p.default_model}
                    </span>
                  )}
                </div>
                <p className="mt-0.5 truncate font-mono text-xs text-foreground-tertiary">
                  {p.base_url || p.id}
                </p>
                {(p.capabilities?.length ?? 0) > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(p.capabilities ?? []).map((cap) => (
                      <Badge key={cap} variant={capabilityVariant(cap)} size="sm">
                        {capabilityLabel(cap)}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-foreground-tertiary">
            {defaultProvider
              ? `Moteur actif : ${defaultProvider.name} — défini par le Core (PUT /providers/{id}/default).`
              : "Aucun moteur par défaut défini — choisissez-le dans le workspace Providers."}
          </p>
        </>
      )}
    </div>
  );
}
