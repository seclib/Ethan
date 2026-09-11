/**
 * ETHAN WebUI — AI Settings Sections (recovery)
 *
 * Sections réelles branchées sur les API Core/Runtime.  Aucune valeur locale :
 * chaque section lit l'état backend et les mutations passent par l'API.
 */

"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Loader2,
  Save,
  CheckCircle2,
  XCircle,
  AudioLines,
  Route as RouteIcon,
} from "lucide-react";
import {
  getRagConfig,
  getRagStatus,
  updateRagConfig,
  type RagConfig,
  type RagConfigResponse,
} from "@/lib/api/rag";
import {
  listProviders,
  testProviderConnection,
  type Provider,
} from "@/lib/api/providers";
import { useUIStore } from "@/store/ui.store";

/* ── Shared scaffold ───────────────────────────────────────────── */

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-xl font-bold text-foreground">{title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
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

function Row({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
      <div>
        <span className="text-sm text-foreground-secondary">{title}</span>
        {description && (
          <span className="block text-xs text-foreground-tertiary">{description}</span>
        )}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

/* ── Embeddings — model selection + engine status ─────────────── */

export function EmbeddingsSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data, isLoading } = useQuery({
    queryKey: ["settings-rag-config"],
    queryFn: () => getRagConfig(),
  });

  const [draft, setDraft] = React.useState<RagConfig | null>(null);
  React.useEffect(() => {
    if (data?.config) setDraft({ ...data.config });
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: (cfg: RagConfig) =>
      updateRagConfig({ embedding_model: cfg.embedding_model ?? "" }),
    onSuccess: (result: RagConfigResponse) => {
      queryClient.invalidateQueries({ queryKey: ["settings-rag-config"] });
      addToast({ type: "success", message: "Modèle d'embedding enregistré" });
      setDraft({ ...result.config });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec" }),
  });

  if (isLoading || !data || !draft) {
    return <div className="p-6"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>;
  }

  const dirty = draft.embedding_model !== (data.config.embedding_model ?? "");

  return (
    <div className="p-6">
      <SectionHeader
        title="Embeddings"
        description="Modèle d'embedding utilisé par le pipeline RAG"
      />
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label="Mode" value={data.stats.embedding_mode === "llm" ? "LLM" : "Fallback textuel"} />
        <StatCard label="Modèle actif" value={data.stats.embedding_model ?? "aucun"} />
        <StatCard label="Embeddings indexés" value={data.stats.indexed_embeddings ? "Oui" : "Non"} />
      </div>

      <div className="max-w-xl space-y-3">
        <Row
          title="Modèle d'embedding"
          description="Nom du modèle (ex: nomic-embed-text). Vide = fallback textuel."
        >
          <Input
            className="w-64 font-mono text-xs"
            placeholder="nomic-embed-text"
            value={draft.embedding_model ?? ""}
            onChange={(e) => setDraft({ ...draft, embedding_model: e.target.value || null })}
          />
        </Row>
        {data.stats.embedding_mode === "textual-fallback" && data.config.embedding_model && (
          <p className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-amber-400">
            ⚠ Modèle configuré mais embeddings non disponibles (provider hors ligne).
          </p>
        )}
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
/* ── Vector Database — backend + config + connection status ────── */

const VECTOR_BACKENDS = [
  { id: "memory", label: "Mémoire (in-process)", hint: "Fallback historique, aucune dépendance." },
  { id: "chromadb", label: "ChromaDB", hint: "HTTP ou persistant (pip install chromadb)." },
  { id: "qdrant", label: "Qdrant", hint: "Serveur vectoriel (pip install qdrant-client)." },
];

export function VectorDatabaseSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data, isLoading } = useQuery({
    queryKey: ["settings-rag-config"],
    queryFn: () => getRagConfig(),
  });
  const { data: status } = useQuery({
    queryKey: ["settings-rag-status"],
    queryFn: () => getRagStatus(),
  });

  const [backend, setBackend] = React.useState("memory");
  const [backendConfig, setBackendConfig] = React.useState("");
  React.useEffect(() => {
    if (data?.config) {
      setBackend(data.config.vector_backend || "memory");
      setBackendConfig(JSON.stringify(data.config.vector_backend_config ?? {}, null, 2));
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: () => {
      let parsed: Record<string, unknown> = {};
      if (backendConfig.trim()) {
        try {
          parsed = JSON.parse(backendConfig) as Record<string, unknown>;
        } catch {
          throw new Error("Configuration JSON invalide");
        }
      }
      return updateRagConfig({ vector_backend: backend, vector_backend_config: parsed });
    },
    onSuccess: (result: RagConfigResponse) => {
      queryClient.invalidateQueries({ queryKey: ["settings-rag-config"] });
      queryClient.invalidateQueries({ queryKey: ["settings-rag-status"] });
      addToast({ type: "success", message: `Backend vectoriel « ${result.config.vector_backend} » enregistré` });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec" }),
  });

  if (isLoading || !data) {
    return <div className="p-6"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>;
  }

  const active = data.config.vector_backend || "memory";
  const dirty = backend !== active || backendConfig !== JSON.stringify(data.config.vector_backend_config ?? {}, null, 2);

  return (
    <div className="p-6">
      <SectionHeader
        title="Vector Database"
        description="Backend vectoriel réellement supporté par le moteur RAG Core"
      />
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label="Backend actif" value={active} />
        <StatCard label="Documents" value={data.stats.documents} />
        <StatCard label="Chunks" value={data.stats.chunks} />
      </div>

      <div className="max-w-xl space-y-3">
        <Row title="Backend vectoriel" description="Sélection déclenche la ré-indexation des documents chargés.">
          <select
            className="w-64 rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 text-sm text-foreground"
            value={backend}
            onChange={(e) => setBackend(e.target.value)}
          >
            {VECTOR_BACKENDS.map((b) => (
              <option key={b.id} value={b.id}>{b.label}</option>
            ))}
          </select>
        </Row>
        <p className="text-xs text-foreground-tertiary">
          {VECTOR_BACKENDS.find((b) => b.id === backend)?.hint}
        </p>
        <Row title="Configuration (JSON)" description="ex: {&quot;url&quot;: &quot;http://localhost:6333&quot;} pour Qdrant">
          <textarea
            className="w-64 rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 font-mono text-xs text-foreground"
            rows={4}
            value={backendConfig}
            onChange={(e) => setBackendConfig(e.target.value)}
          />
        </Row>
        {status?.embedding_mode === "textual-fallback" && backend !== "memory" && (
          <p className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-amber-400">
            ⚠ Backend configuré mais indisponible (package manquant ou endpoint hors ligne).
          </p>
        )}
      </div>

      <div className="mt-6 flex justify-end">
        <Button
          variant="primary"
          onClick={() => saveMutation.mutate()}
          disabled={!dirty || saveMutation.isPending}
        >
          {saveMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          <span className="ml-1">Enregistrer</span>
        </Button>
      </div>
    </div>
  );
}
/* ── Chunking — splitting strategy + preview ───────────────────── */

const SPLITTING_STRATEGIES = [
  { id: "character", label: "Caractères", hint: "Découpe à taille fixe (chunk_size)." },
  { id: "sentence", label: "Phrases", hint: "Découpe aux frontières de phrases." },
  { id: "paragraph", label: "Paragraphes", hint: "Découpe aux sauts de paragraphe." },
];

export function ChunkingSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [previewText, setPreviewText] = React.useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["settings-rag-config"],
    queryFn: () => getRagConfig(),
  });
  const [draft, setDraft] = React.useState<RagConfig | null>(null);
  React.useEffect(() => {
    if (data?.config) setDraft({ ...data.config });
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: (cfg: RagConfig) =>
      updateRagConfig({
        splitting_strategy: cfg.splitting_strategy || "character",
        chunk_size: cfg.chunk_size,
        chunk_overlap: cfg.chunk_overlap,
      }),
    onSuccess: (result: RagConfigResponse) => {
      queryClient.invalidateQueries({ queryKey: ["settings-rag-config"] });
      addToast({ type: "success", message: "Découpage enregistré" });
      setDraft({ ...result.config });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec" }),
  });

  if (isLoading || !data || !draft) {
    return <div className="p-6"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>;
  }

  const strategy = draft.splitting_strategy || "character";
  const estimatedChunks =
    previewText.length > 0
      ? Math.max(1, Math.ceil((previewText.length - draft.chunk_overlap) / Math.max(1, draft.chunk_size - draft.chunk_overlap)))
      : null;
  const dirty =
    strategy !== (data.config.splitting_strategy || "character") ||
    draft.chunk_size !== data.config.chunk_size ||
    draft.chunk_overlap !== data.config.chunk_overlap;
return (
    <div className="p-6">
      <SectionHeader
        title="Text Splitting & Chunking"
        description="Comment l'ingestion découpe les documents avant embedding"
      />
      <div className="max-w-xl space-y-3">
        <Row title="Stratégie de découpage" description="Appliquée aux prochaines ingestions.">
          <select
            className="w-64 rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 text-sm text-foreground"
            value={strategy}
            onChange={(e) => setDraft({ ...draft, splitting_strategy: e.target.value })}
          >
            {SPLITTING_STRATEGIES.map((s) => (
              <option key={s.id} value={s.id}>{s.label}</option>
            ))}
          </select>
        </Row>
        <p className="text-xs text-foreground-tertiary">
          {SPLITTING_STRATEGIES.find((s) => s.id === strategy)?.hint}
        </p>
        <Row title="Chunk size" description="Nombre de caractères par chunk.">
          <Input
            type="number"
            min={1}
            className="w-32"
            value={String(draft.chunk_size)}
            onChange={(e) => setDraft({ ...draft, chunk_size: Number(e.target.value) })}
          />
        </Row>
        <Row title="Chunk overlap" description="Chevauchement entre chunks (caractères).">
          <Input
            type="number"
            min={0}
            className="w-32"
            value={String(draft.chunk_overlap)}
            onChange={(e) => setDraft({ ...draft, chunk_overlap: Number(e.target.value) })}
          />
        </Row>

        <div className="rounded-lg border border-line-1 bg-bg-1 p-4">
          <p className="mb-2 text-xs font-medium text-foreground-secondary">
            Aperçu — collez un texte pour estimer le nombre de chunks générés
          </p>
          <textarea
            className="w-full rounded-lg border border-line-1 bg-bg-1 px-3 py-2 text-xs text-foreground"
            rows={4}
            placeholder="Collez le contenu d'un document…"
            value={previewText}
            onChange={(e) => setPreviewText(e.target.value)}
          />
          {estimatedChunks !== null && (
            <p className="mt-2 text-xs text-foreground-secondary">
              ≈ <span className="font-medium text-foreground">{estimatedChunks}</span> chunk(s)
              avec cette configuration
            </p>
          )}
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

/* ── Reranking — real retrieval limits (no invented strategy) ──── */

export function RerankingSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data, isLoading } = useQuery({
    queryKey: ["settings-rag-config"],
    queryFn: () => getRagConfig(),
  });
  const [draft, setDraft] = React.useState<RagConfig | null>(null);
  React.useEffect(() => {
    if (data?.config) setDraft({ ...data.config });
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: (cfg: RagConfig) =>
      updateRagConfig({ top_k: cfg.top_k, max_context_chars: cfg.max_context_chars }),
    onSuccess: (result: RagConfigResponse) => {
      queryClient.invalidateQueries({ queryKey: ["settings-rag-config"] });
      addToast({ type: "success", message: "Retrieval enregistré" });
      setDraft({ ...result.config });
    },
    onError: (err) =>
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec" }),
  });

  if (isLoading || !data || !draft) {
    return <div className="p-6"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>;
  }

  const dirty = draft.top_k !== data.config.top_k || draft.max_context_chars !== data.config.max_context_chars;
return (
    <div className="p-6">
      <SectionHeader
        title="Retrieval & Reranking"
        description="Limites du retrieval (top_k, budget de contexte) — la stratégie vient du Core"
      />
      <div className="max-w-xl space-y-3">
        <Row title="Top K" description="Nombre de chunks récupérés par requête.">
          <Input
            type="number"
            min={1}
            className="w-32"
            value={String(draft.top_k)}
            onChange={(e) => setDraft({ ...draft, top_k: Number(e.target.value) })}
          />
        </Row>
        <Row title="Contexte max (caractères)" description="Budget de contexte transmis au modèle.">
          <Input
            type="number"
            min={100}
            className="w-32"
            value={String(draft.max_context_chars)}
            onChange={(e) => setDraft({ ...draft, max_context_chars: Number(e.target.value) })}
          />
        </Row>
        <Row title="Stratégie de recherche" description="Fournie par le Core — aucune inventée ici.">
          <span className="rounded-full bg-bg-2 px-3 py-1 text-xs font-medium text-foreground">
            {draft.strategy}
          </span>
        </Row>
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

/* ── Model Routers — providers/capacités réels ────────────────── */

export function ModelRoutersSection() {
  const { data: providers = [], isLoading } = useQuery({
    queryKey: ["settings-providers"],
    queryFn: () => listProviders(),
  });

  const routeBadge = (p: Provider, cap: string) => {
    const has = Array.isArray(p.capabilities) && (p.capabilities as string[]).includes(cap);
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] uppercase ${
          has ? "bg-green-500/10 text-green-400" : "bg-bg-2 text-foreground-tertiary"
        }`}
      >
        {has ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
        {cap}
      </span>
    );
  };

  return (
    <div className="p-6">
      <SectionHeader
        title="Model Routers"
        description="Providers disponibles et leurs capacités (routing réel côté Core)"
      />
      {isLoading ? (
        <div className="p-4"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
      ) : providers.length === 0 ? (
        <p className="text-sm text-foreground-tertiary">Aucun provider enregistré.</p>
      ) : (
        <div className="space-y-2">
          {providers.map((p: Provider) => (
            <div
              key={p.id}
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium text-foreground">{p.name}</span>
                  {p.is_default && (
                    <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] uppercase text-accent">default</span>
                  )}
                </div>
                <p className="mt-0.5 truncate font-mono text-xs text-foreground-tertiary">
                  {p.type} · {p.default_model || "aucun modèle par défaut"}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-1">
                {routeBadge(p, "llm")}
                {routeBadge(p, "embedding")}
                {routeBadge(p, "transcription")}
                {routeBadge(p, "speech_to_text")}
                {routeBadge(p, "vision")}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
/* ── Speech-to-Text — providers capables + test ────────────────── */

export function SpeechToTextSection() {
  const { data: providers = [], isLoading } = useQuery({
    queryKey: ["settings-providers"],
    queryFn: () => listProviders(),
  });
  const [testResult, setTestResult] = React.useState<string | null>(null);
  const [testingId, setTestingId] = React.useState<string | null>(null);

  const capable = providers.filter(
    (p: Provider) =>
      Array.isArray(p.capabilities) &&
      ((p.capabilities as string[]).includes("transcription") ||
        (p.capabilities as string[]).includes("speech_to_text")),
  );

  const runTest = async (id: string) => {
    setTestingId(id);
    setTestResult(null);
    try {
      const res = await testProviderConnection(id);
      setTestResult(`${res.provider_id}: ${res.status} — ${res.message}`);
    } catch (err) {
      setTestResult(err instanceof Error ? err.message : "Échec du test");
    } finally {
      setTestingId(null);
    }
  };

  return (
    <div className="p-6">
      <SectionHeader
        title="Speech-to-Text & Transcription"
        description="Providers capables de transcription — modèle sélectionné par le Core"
      />
      {isLoading ? (
        <div className="p-4"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
      ) : capable.length === 0 ? (
        <p className="text-sm text-foreground-tertiary">
          Aucun provider ne déclare la transcription. Ajoutez un provider compatible (ex: OpenAI Whisper)
          depuis <span className="font-medium text-foreground">AI Providers</span>.
        </p>
      ) : (
        <div className="space-y-2">
          {capable.map((p: Provider) => (
            <div
              key={p.id}
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <AudioLines className="h-4 w-4 text-foreground-tertiary" />
                  <span className="truncate text-sm font-medium text-foreground">{p.name}</span>
                  {p.default_model && (
                    <span className="rounded-full bg-bg-2 px-2 py-0.5 text-[10px] text-foreground-tertiary">
                      modèle: {p.default_model}
                    </span>
                  )}
                </div>
                <p className="mt-0.5 truncate text-xs text-foreground-tertiary">{p.type}</p>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => runTest(p.id)}
                disabled={testingId === p.id}
              >
                {testingId === p.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RouteIcon className="h-3.5 w-3.5" />}
                <span className="ml-1">Tester</span>
              </Button>
            </div>
          ))}
        </div>
      )}
      {testResult && (
        <div className="mt-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3 text-sm text-foreground-secondary">
          {testResult}
        </div>
      )}
    </div>
  );
}