/**
 * ETHAN WebUI — Sections Settings réellement servies par ETHAN Core.
 *
 * Remplace les écrans « fantômes » historiques (formulaires factices jamais
 * branchés : Default Model gpt-4/claude-3, Temperature, 2FA, Telemetry,
 * Custom CSS…). Règles appliquées (AGENTS.md + audit
 * docs/design/2026-09-30-webui-settings-honesty.md) :
 *
 *  - chaque contrôle affiché lit/écrit une capacité RÉELLE du Core ;
 *  - les préférences purement interface (mode de chat, vue Library) sont
 *    persistées côté WebUI et réellement consommées par l'interface ;
 *  - les surfaces gérées dans un workspace dédié (2FA, utilisateurs, audit,
 *    logs, providers…) sont RÉVÉLÉES par un état live + un lien — jamais
 *    dupliquées, jamais réinventées ;
 *  - états explicites : chargement, vide, erreur, dégradé.
 */

"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui.store";
import {
  CHAT_MODES,
  REASONING_EFFORTS,
  useChatModeStore,
  type ChatModeValue,
} from "@/store/chat-mode.store";
import { useLibraryStore } from "@/store/library.store";
import {
  listSearchTypes,
  search as runSearch,
  type SearchResponse,
  type SearchType,
} from "@/lib/api/search";
import {
  createReminder,
  deleteReminder,
  disableReminder,
  enableReminder,
  listReminders,
  type Reminder,
} from "@/lib/api/reminders";
import {
  fetchDetailedHealth,
  fetchDiagnostics,
  type DiagnosticsReport,
} from "@/lib/api/diagnostics";
import { getSecurityStatus, getTwoFactorStatus } from "@/lib/api/security";
import { SHORTCUTS } from "@/config/shortcuts";
import {
  AlertCircle,
  Bell,
  CheckCircle2,
  ExternalLink,
  Keyboard,
  LayoutGrid,
  List,
  Loader2,
  Plus,
  Power,
  PowerOff,
  RefreshCw,
  Search,
  Trash2,
  XCircle,
} from "lucide-react";

// ── Shared building blocks ───────────────────────────────────────────

export function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-xl font-bold text-foreground">{title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

function SectionTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h3
      className={cn(
        "mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-tertiary",
        className,
      )}
    >
      {children}
    </h3>
  );
}

/** Encart d'explication — dit toujours qui applique quoi (Core vs interface). */
export function Note({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-6 max-w-3xl rounded-lg border border-line-1 bg-bg-1 px-4 py-3 text-xs leading-relaxed text-muted-foreground">
      {children}
    </p>
  );
}

function SectionLoading() {
  return (
    <div className="flex items-center justify-center py-10 text-foreground-tertiary">
      <Loader2 className="h-5 w-5 animate-spin" />
    </div>
  );
}

/** État d'erreur explicite (aucune donnée simulée en remplacement). */
function ErrorNote({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-line-1 bg-bg-1 px-4 py-3 text-sm text-foreground-secondary">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--red)]" />
      <span>{message}</span>
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

/** Lien vers le workspace qui possède réellement la capacité (source unique). */
export function WorkspaceLink({ href, label }: { href: string; label: string }) {
  return (
    <a href={href}>
      <Button variant="secondary" size="sm">
        <ExternalLink className="h-3.5 w-3.5" />
        <span className="ml-1">{label}</span>
      </Button>
    </a>
  );
}

// ── Chat — mode conversationnel par défaut (préférence réelle) ───────
//
// Source unique : chat-mode.store (consommé par ChatModeToggle + le payload
// chat `mode` / `reasoning_effort` dans app/page.tsx). Le Core arbitre
// ensuite la valeur selon les capacités du modèle cible.

export function ChatSection() {
  const mode = useChatModeStore((s) => s.mode);
  const reasoningEffort = useChatModeStore((s) => s.reasoningEffort);
  const setMode = useChatModeStore((s) => s.setMode);
  const setReasoningEffort = useChatModeStore((s) => s.setReasoningEffort);

  return (
    <div className="p-6">
      <SectionHeader
        title="Chat"
        description="Mode conversationnel et effort de raisonnement par défaut des nouvelles conversations."
      />

      <SectionTitle>Mode par défaut</SectionTitle>
      <div className="grid max-w-3xl gap-3 sm:grid-cols-3">
        {(Object.keys(CHAT_MODES) as ChatModeValue[]).map((id) => {
          const meta = CHAT_MODES[id];
          const active = mode === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setMode(id)}
              aria-pressed={active}
              className={cn(
                "rounded-lg border px-4 py-3 text-left transition-colors",
                active
                  ? "border-accent bg-accent/10"
                  : "border-line-1 bg-bg-1 hover:border-line-3",
              )}
            >
              <span className="flex items-center justify-between text-sm font-medium text-foreground">
                {meta.label}
                {active && <CheckCircle2 className="h-4 w-4 text-accent" />}
              </span>
              <span className="mt-1 block text-xs text-muted-foreground">{meta.description}</span>
            </button>
          );
        })}
      </div>

      <SectionTitle className="mt-8">Effort de raisonnement</SectionTitle>
      <div className="flex flex-wrap gap-2">
        {REASONING_EFFORTS.map(({ value, label }) => (
          <Button
            key={value}
            size="sm"
            variant={reasoningEffort === value ? "primary" : "secondary"}
            aria-pressed={reasoningEffort === value}
            onClick={() => setReasoningEffort(value)}
          >
            {label}
          </Button>
        ))}
      </div>

      <Note>
        Ces préférences sont envoyées à ETHAN Core à chaque message
        (<span className="font-mono">mode</span>,{" "}
        <span className="font-mono">reasoning_effort</span>) ; le Core arbitre selon les
        capacités réelles du modèle. Le sélecteur du composer reste prioritaire pour la
        conversation en cours.
      </Note>
    </div>
  );
}


// ── Search — console de recherche globale (Core /v1/search) ─────────

export function SearchSection() {
  const [query, setQuery] = React.useState("");
  const [type, setType] = React.useState<SearchType>("knowledge");
  const [submitted, setSubmitted] = React.useState("");

  // Types réellement supportés par le Core (aucune liste inventée côté UI).
  const typesQuery = useQuery({
    queryKey: ["search-types"],
    queryFn: listSearchTypes,
    staleTime: Infinity,
  });

  const resultsQuery = useQuery<SearchResponse>({
    queryKey: ["search-console", submitted, type],
    queryFn: () => runSearch(submitted, type, 20),
    enabled: submitted.length > 0,
    retry: false,
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (q.length > 0) setSubmitted(q);
  };

  return (
    <div className="p-6">
      <SectionHeader
        title="Search"
        description="Rechercher dans ETHAN (knowledge, library, conversations, web) — moteur du Core."
      />

      <form onSubmit={submit} className="flex max-w-3xl flex-wrap items-center gap-2">
        <div className="relative min-w-56 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-tertiary" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher…"
            aria-label="Requête de recherche"
            className="pl-9"
          />
        </div>
        <select
          value={type}
          onChange={(e) => setType(e.target.value as SearchType)}
          aria-label="Type de recherche"
          className="rounded-md border border-line-1 bg-[var(--panel)] px-3 py-2 text-sm text-foreground"
        >
          <option value="knowledge">knowledge</option>
          <option value="library">library</option>
          <option value="conversation">conversation</option>
          <option value="web">web</option>
          {typesQuery.data?.types
            .filter((t) => !["knowledge", "library", "conversation", "web"].includes(t))
            .map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
        </select>
        <Button type="submit" size="sm" disabled={query.trim().length === 0}>
          Rechercher
        </Button>
      </form>

      {typesQuery.isError && (
        <div className="mt-3">
          <ErrorNote message="Types de recherche indisponibles (Core injoignable) — la recherche utilisera le type par défaut." />
        </div>
      )}

      <div className="mt-5 max-w-3xl">
        {submitted.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Saisissez une requête pour interroger le moteur du Core. La command palette
            (Ctrl+K) reste le raccourci de navigation globale.
          </p>
        )}
        {resultsQuery.isFetching && <SectionLoading />}
        {resultsQuery.isError && (
          <ErrorNote
            message={`Recherche impossible : ${
              resultsQuery.error instanceof Error ? resultsQuery.error.message : "erreur Core"
            }`}
          />
        )}
        {resultsQuery.data && !resultsQuery.isFetching && (
          <>
            <p className="mb-2 text-xs text-muted-foreground" data-testid="search-total">
              {resultsQuery.data.total} résultat(s) pour « {resultsQuery.data.query} » ({resultsQuery.data.type})
            </p>
            {resultsQuery.data.results.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun résultat.</p>
            ) : (
              <ul className="space-y-2">
                {resultsQuery.data.results.map((result) => (
                  <li
                    key={`${result.type}-${result.id}`}
                    className="rounded-lg border border-line-1 bg-bg-1 px-4 py-3"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground">{result.title}</span>
                      <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[11px] text-accent">
                        {result.type}
                      </span>
                    </div>
                    {(result.source || result.description) && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        {result.source || result.description}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>

      <Note>
        Cette console interroge le moteur de recherche d&apos;ETHAN Core
        (<span className="font-mono">/v1/search</span>). Elle ne stocke rien : les
        résultats sont servis par les managers Core (Knowledge, ChatStore, RAG).
      </Note>
    </div>
  );
}


// ── Reminders — rappels réellement planifiés par le Core (/reminders) ─

/** Fuseau du navigateur — affiché, jamais imposé (le Core stocke le champ). */
const BROWSER_TIMEZONE =
  typeof Intl !== "undefined" ? Intl.DateTimeFormat().resolvedOptions().timeZone : "UTC";

function reminderWhen(reminder: Reminder): string {
  if (reminder.schedule) return `Cron ${reminder.schedule}`;
  if (reminder.fire_at) return new Date(reminder.fire_at).toLocaleString();
  return "—";
}

export function RemindersSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [createOpen, setCreateOpen] = React.useState(false);
  const [pendingDelete, setPendingDelete] = React.useState<Reminder | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["reminders"],
    queryFn: () => listReminders(),
    retry: false,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["reminders"] });

  const toggleMutation = useMutation({
    mutationFn: (reminder: Reminder) =>
      reminder.enabled ? disableReminder(reminder.id) : enableReminder(reminder.id),
    onSuccess: invalidate,
    onError: (err) =>
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Impossible de modifier le rappel",
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteReminder(id),
    onSuccess: () => {
      invalidate();
      addToast({ type: "success", message: "Rappel supprimé" });
    },
    onError: (err) =>
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Impossible de supprimer le rappel",
      }),
  });

  const reminders = data ?? [];

  return (
    <div className="p-6">
      <SectionHeader
        title="Reminders"
        description="Rappels planifiés par ETHAN Core (cron ou date unique) — le WebUI affiche et déclenche."
      />

      <div className="mb-4 flex items-center gap-2">
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" />
          <span className="ml-1">Nouveau rappel</span>
        </Button>
        <Button size="sm" variant="outline" onClick={invalidate} aria-label="Rafraîchir les rappels">
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </div>

      {isLoading && <SectionLoading />}
      {error && (
        <ErrorNote
          message={`Rappels indisponibles : ${
            error instanceof Error ? error.message : "erreur Core"
          }`}
        />
      )}
      {!isLoading && !error && reminders.length === 0 && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Bell className="h-4 w-4" />
          Aucun rappel dans ETHAN Core.
        </div>
      )}
      {reminders.length > 0 && (
        <ul className="max-w-3xl space-y-2">
          {reminders.map((reminder) => (
            <li
              key={reminder.id}
              className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium text-foreground">
                    {reminder.title || reminder.id}
                  </span>
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-[11px]",
                      reminder.enabled
                        ? "bg-[var(--green)]/10 text-[var(--green)]"
                        : "bg-[var(--panel-hover)] text-muted-foreground",
                    )}
                  >
                    {reminder.enabled ? "actif" : "inactif"}
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {reminderWhen(reminder)} · {reminder.timezone}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label={
                    reminder.enabled ? `Désactiver ${reminder.title}` : `Activer ${reminder.title}`
                  }
                  disabled={toggleMutation.isPending}
                  onClick={() => toggleMutation.mutate(reminder)}
                >
                  {reminder.enabled ? (
                    <Power className="h-4 w-4" />
                  ) : (
                    <PowerOff className="h-4 w-4" />
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label={`Supprimer ${reminder.title}`}
                  onClick={() => setPendingDelete(reminder)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <CreateReminderDialog open={createOpen} onOpenChange={setCreateOpen} onCreated={invalidate} />

      <ConfirmDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open) setPendingDelete(null);
        }}
        title="Supprimer ce rappel ?"
        message={
          pendingDelete
            ? `« ${pendingDelete.title || pendingDelete.id} » sera retiré du planificateur Core.`
            : undefined
        }
        confirmLabel="Supprimer"
        destructive
        onConfirm={() => {
          if (pendingDelete) deleteMutation.mutate(pendingDelete.id);
          setPendingDelete(null);
        }}
      />

      <Note>
        La planification (cron 5 champs ou date unique), l&apos;exécution et les fuseaux
        sont garantis par ETHAN Core. Le WebUI ne planifie jamais côté navigateur.
      </Note>
    </div>
  );
}


function CreateReminderDialog({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}) {
  const addToast = useUIStore((s) => s.addToast);
  const [title, setTitle] = React.useState("");
  const [kind, setKind] = React.useState<"once" | "recurring">("once");
  const [fireAt, setFireAt] = React.useState("");
  const [schedule, setSchedule] = React.useState("0 9 * * *");
  const [formError, setFormError] = React.useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      createReminder({
        title: title.trim(),
        timezone: BROWSER_TIMEZONE,
        ...(kind === "once"
          ? { fire_at: new Date(fireAt).toISOString() }
          : { schedule: schedule.trim() }),
      }),
    onSuccess: () => {
      onCreated();
      addToast({ type: "success", message: "Rappel créé" });
      onOpenChange(false);
      setTitle("");
      setFireAt("");
      setFormError(null);
    },
    onError: (err) =>
      setFormError(err instanceof Error ? err.message : "Création refusée par le Core"),
  });

  const handleSubmit = () => {
    if (title.trim().length === 0) {
      setFormError("Un titre est requis.");
      return;
    }
    if (kind === "once" && fireAt.length === 0) {
      setFormError("Choisissez la date et l'heure de déclenchement.");
      return;
    }
    if (kind === "recurring" && schedule.trim().length === 0) {
      setFormError("Une expression cron (5 champs) est requise.");
      return;
    }
    setFormError(null);
    createMutation.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title="Nouveau rappel">
      <div className="space-y-4">
        <div className="space-y-1">
          <label className="text-sm font-medium" htmlFor="reminder-title">
            Titre
          </label>
          <Input
            id="reminder-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Relancer la revue hebdomadaire"
          />
        </div>

        <div className="space-y-1">
          <span className="text-sm font-medium">Déclenchement</span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={kind === "once" ? "primary" : "secondary"}
              onClick={() => setKind("once")}
            >
              Une fois
            </Button>
            <Button
              size="sm"
              variant={kind === "recurring" ? "primary" : "secondary"}
              onClick={() => setKind("recurring")}
            >
              Récurrent (cron)
            </Button>
          </div>
        </div>

        {kind === "once" ? (
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="reminder-fire-at">
              Date et heure
            </label>
            <Input
              id="reminder-fire-at"
              type="datetime-local"
              value={fireAt}
              onChange={(e) => setFireAt(e.target.value)}
            />
          </div>
        ) : (
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="reminder-schedule">
              Expression cron (5 champs)
            </label>
            <Input
              id="reminder-schedule"
              value={schedule}
              onChange={(e) => setSchedule(e.target.value)}
              className="font-mono"
              placeholder="0 9 * * *"
            />
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          Fuseau transmis au Core : <span className="font-mono">{BROWSER_TIMEZONE}</span>
        </p>

        {formError && <ErrorNote message={formError} />}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={handleSubmit} loading={createMutation.isPending}>
            Créer
          </Button>
        </div>
      </div>
    </Dialog>
  );
}


// ── Library — préférence d'affichage réelle (consommée par l'onglet Library) ──

export function LibrarySection() {
  const viewMode = useLibraryStore((s) => s.viewMode);
  const setViewMode = useLibraryStore((s) => s.setViewMode);

  return (
    <div className="p-6">
      <SectionHeader
        title="Library"
        description="Préférences d'affichage de la bibliothèque (onglet Library de /knowledge) — agrégation des ressources du Core."
      />

      <SectionTitle>Vue par défaut</SectionTitle>
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant={viewMode === "grid" ? "primary" : "secondary"}
          aria-pressed={viewMode === "grid"}
          onClick={() => setViewMode("grid")}
        >
          <LayoutGrid className="h-4 w-4" />
          <span className="ml-1">Grille</span>
        </Button>
        <Button
          size="sm"
          variant={viewMode === "list" ? "primary" : "secondary"}
          aria-pressed={viewMode === "list"}
          onClick={() => setViewMode("list")}
        >
          <List className="h-4 w-4" />
          <span className="ml-1">Liste</span>
        </Button>
      </div>

      <div className="mt-6">
        {/* La Library est un onglet de Knowledge : cible directe, pas de détour. */}
        <WorkspaceLink href="/knowledge?view=library" label="Ouvrir la Library" />
      </div>

      <Note>
        Préférence d&apos;interface : elle est appliquée à l&apos;ouverture de la
        bibliothèque. Les ressources affichées (documents RAG, knowledge, collections,
        images) restent servies par ETHAN Core — aucun stockage parallèle.
      </Note>
    </div>
  );
}

// ── System — santé réelle du runtime (Core) + workspaces de supervision ─

export function SystemSection() {
  const healthQuery = useQuery({
    queryKey: ["health-detailed"],
    queryFn: fetchDetailedHealth,
    retry: false,
    refetchInterval: 30_000,
  });
  const diagQuery = useQuery({
    queryKey: ["diagnostics"],
    queryFn: () => fetchDiagnostics(),
    retry: false,
  });

  const health = healthQuery.data;
  const diagReport: DiagnosticsReport | null =
    diagQuery.data && !("ok" in diagQuery.data) ? diagQuery.data : null;

  return (
    <div className="p-6">
      <SectionHeader
        title="System"
        description="État réel du runtime ETHAN (dépendances Core) et accès à la supervision."
      />

      <div className="mb-3 flex items-center gap-3">
        <SectionTitle className="mb-0">Dépendances</SectionTitle>
        <Button size="sm" variant="outline" onClick={() => healthQuery.refetch()} aria-label="Re-vérifier">
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </div>

      {healthQuery.isLoading && <SectionLoading />}
      {healthQuery.isError && (
        <ErrorNote
          message={`Health Core indisponible : ${
            healthQuery.error instanceof Error ? healthQuery.error.message : "erreur réseau"
          }`}
        />
      )}
      {health && (
        <ul className="max-w-3xl space-y-2">
          {Object.entries(health.checks).map(([name, status]) => {
            const ok = status === "connected";
            return (
              <li
                key={name}
                className="flex items-center justify-between gap-4 rounded-lg border border-line-1 bg-bg-1 px-4 py-2.5"
              >
                <span className="flex items-center gap-2 text-sm text-foreground-secondary">
                  <StatusDot ok={ok} />
                  <span className="font-mono">{name}</span>
                </span>
                <span className={cn("text-xs", ok ? "text-[var(--green)]" : "text-[var(--red)]")}>
                  {ok ? "connecté" : status}
                </span>
              </li>
            );
          })}
        </ul>
      )}

      {diagReport && (
        <p className="mt-4 text-xs text-muted-foreground">
          Diagnostics Core : {diagReport.summary.status} ({diagReport.summary.total} composants)
        </p>
      )}

      <div className="mt-6 flex flex-wrap gap-2">
        <WorkspaceLink href="/diagnostics" label="Diagnostics" />
        <WorkspaceLink href="/monitoring" label="Monitoring" />
        <WorkspaceLink href="/logs" label="Logs" />
      </div>

      <Note>
        Le niveau de log et le nombre de workers sont des paramètres de DÉPLOIEMENT
        (variables d&apos;environnement Core) : ils s&apos;appliquent au démarrage, jamais à
        chaud depuis l&apos;interface. Les métriques système (CPU, mémoire, GPU) sont
        exposées par Diagnostics/Monitoring.
      </Note>
    </div>
  );
}


// ── Security — état réel (lecture seule) + workspace de gestion ──────

export function SecuritySection() {
  const secQuery = useQuery({
    queryKey: ["security-status"],
    queryFn: getSecurityStatus,
    retry: false,
  });
  const tfaQuery = useQuery({
    queryKey: ["2fa"],
    queryFn: getTwoFactorStatus,
    retry: false,
  });

  const sec = secQuery.data;

  return (
    <div className="p-6">
      <SectionHeader
        title="Security"
        description="État réel du système de sécurité ETHAN — lecture seule ; les politiques sont appliquées par le Core."
      />

      <SectionTitle>Double authentification (2FA)</SectionTitle>
      <div className="max-w-xl rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
        {tfaQuery.isLoading && <SectionLoading />}
        {tfaQuery.isError && (
          <p className="flex items-center gap-2 text-sm text-foreground-secondary">
            <XCircle className="h-4 w-4 text-[var(--amber)]" />
            Statut 2FA indisponible (droits insuffisants ou Core injoignable).
          </p>
        )}
        {tfaQuery.data && (
          <p className="flex items-center gap-2 text-sm text-foreground-secondary">
            {tfaQuery.data.enabled ? (
              <CheckCircle2 className="h-4 w-4 text-[var(--green)]" />
            ) : (
              <XCircle className="h-4 w-4 text-[var(--amber)]" />
            )}
            {tfaQuery.data.enabled
              ? "Activée sur ce compte."
              : tfaQuery.data.pending
                ? "Configuration en attente de confirmation."
                : "Désactivée sur ce compte."}
          </p>
        )}
      </div>

      <SectionTitle className="mt-8">Politiques et audit</SectionTitle>
      {secQuery.isLoading && <SectionLoading />}
      {secQuery.isError && (
        <ErrorNote
          message={`Résumé sécurité indisponible : ${
            secQuery.error instanceof Error ? secQuery.error.message : "erreur Core"
          }`}
        />
      )}
      {sec && (
        <div className="grid max-w-3xl gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
            <p className="text-xs text-muted-foreground">Politiques</p>
            <p className="mt-1 text-lg font-semibold text-foreground">{sec.policies.total}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {Object.entries(sec.policies.by_level)
                .map(([level, count]) => `${level}: ${count}`)
                .join(" · ") || "aucun niveau déclaré"}
            </p>
          </div>
          <div className="rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
            <p className="text-xs text-muted-foreground">Capacités actives</p>
            <p className="mt-1 text-lg font-semibold text-foreground">{sec.capabilities.active}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {sec.capabilities.summary
                ? `${sec.capabilities.summary.allowed} autorisées · ${sec.capabilities.summary.denied} refusées`
                : "aucune évaluation enregistrée"}
            </p>
          </div>
          <div className="rounded-lg border border-line-1 bg-bg-1 px-4 py-3">
            <p className="text-xs text-muted-foreground">Événements d&apos;audit</p>
            <p className="mt-1 text-lg font-semibold text-foreground">{sec.audit.total}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">journal Core</p>
          </div>
        </div>
      )}

      <div className="mt-6">
        <WorkspaceLink href="/security" label="Gérer la sécurité" />
      </div>

      <Note>
        Aucune règle de sécurité n&apos;est modifiable ici : 2FA, utilisateurs, clés API,
        identités et audit sont gérés par le workspace Sécurité (endpoints Core). Le
        WebUI ne fait que révéler l&apos;état.
      </Note>
    </div>
  );
}

// ── Shortcuts — registre réel géré par le WebUI (use-keyboard) ───────

export function ShortcutsSection() {
  return (
    <div className="p-6">
      <SectionHeader
        title="Shortcuts"
        description="Raccourcis clavier de navigation (gérés par l'interface — aucune logique Core)."
      />
      <div className="max-w-3xl space-y-2">
        {SHORTCUTS.map((s) => (
          <div
            key={s.id}
            className="flex items-center justify-between rounded-md border border-line-1 px-4 py-3"
          >
            <div className="flex items-center gap-2">
              <Keyboard className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-foreground">{s.label}</span>
            </div>
            <kbd className="rounded-md bg-[var(--panel)] px-2 py-1 text-xs font-mono text-muted-foreground">
              {s.display}
            </kbd>
          </div>
        ))}
      </div>
    </div>
  );
}

