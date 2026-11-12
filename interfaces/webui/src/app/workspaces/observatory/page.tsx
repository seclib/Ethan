"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  GitBranch,
  Clock,
  Search,
  Database,
  Layers,
  ArrowRight,
  FolderTree,
  Bot,
  Boxes,
} from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { Card } from "@/components/ui/card";
import { listFacts, listMemoryEvents } from "@/lib/api/memory";
import { listCollections } from "@/lib/api/knowledge";
import { listVaultTree, listEngineeringRecords } from "@/lib/api/observatory";
import { staggerStyle } from "@/lib/motion";

export default function ObservatoryPage() {
  const { data: facts = [], isLoading: factsLoading } = useQuery({
    queryKey: ["observa-facts"],
    queryFn: () => listFacts(100),
    staleTime: 60_000,
  });

  const { data: events = [], isLoading: eventsLoading } = useQuery({
    queryKey: ["observa-mem-events"],
    queryFn: () => listMemoryEvents(),
    staleTime: 60_000,
  });

  const { data: collections = [], isLoading: collectionsLoading } = useQuery({
    queryKey: ["observa-collections"],
    queryFn: () => listCollections(),
    staleTime: 60_000,
  });

  const { data: tree } = useQuery({
    queryKey: ["observa-vault-tree"],
    queryFn: () => listVaultTree(),
    staleTime: 5 * 60_000,
  });

  const { data: engineeringRecords = [], isLoading: engineeringRecordsLoading } = useQuery({
    queryKey: ["observa-eng-records"],
    queryFn: () => listEngineeringRecords({ limit: 500 }),
    staleTime: 60_000,
  });

  // Comptés depuis l'arborescence du vault — pas de second moteur d'index.
  const vaultStats = React.useMemo(() => {
    let files = 0;
    let directories = 0;
    let bytes = 0;
    const walk = (node: { type: string; size_bytes?: number; children?: typeof node[] }) => {
      if (node.type === "file") {
        files += 1;
        bytes += node.size_bytes ?? 0;
        return;
      }
      directories += 1;
      for (const child of node.children ?? []) walk(child);
    };
    if (tree) walk(tree);
    return { files, directories, megabytes: (bytes / (1024 * 1024)).toFixed(1) };
  }, [tree]);

  const recentFacts = facts.slice(0, 5);
  const recentEvents = events.slice(0, 5);
  const recentCollections = collections.slice(0, 5);

  return (
    <div className="p-5 md:p-6">
      <PageHeader
        title="DAËNA"
        description="Environnement de mémoire et de connaissances d'ETHAN"
        icon={<Database className="h-5 w-5" />}
      />

      {/* Statistiques noyau — données réelles via l'API Core */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          index={0}
          label="Documents du vault"
          value={vaultStats.files}
          caption={`${vaultStats.directories} dossiers · ${vaultStats.megabytes} Mo`}
          icon={<FolderTree className="h-4 w-4" />}
          loading={!tree}
        />
        <StatTile
          index={1}
          label="Collections knowledge"
          value={collections.length}
          caption="Bases RAG utilisateur"
          icon={<Layers className="h-4 w-4" />}
          loading={collectionsLoading}
        />
        <StatTile
          index={2}
          label="Événements mémoire"
          value={events.length}
          caption="Flux d'ingestion WebUI"
          icon={<Clock className="h-4 w-4" />}
          loading={eventsLoading}
        />
        <StatTile
          index={3}
          label="Enregistrements Engineering Memory"
          value={engineeringRecords.length}
          caption="Décisions · composants · incidents"
          icon={<Database className="h-4 w-4" />}
          loading={engineeringRecordsLoading}
        />
      </div>

      {/* Accès rapides */}
      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <QuickAction index={0} href="/workspaces/observatory/vault" label="Vault" description="Lire et éditer les documents" icon={<BookOpen className="h-5 w-5" />} />
        <QuickAction index={1} href="/workspaces/observatory/graph" label="Graph" description="Explorer le graphe de documents" icon={<GitBranch className="h-5 w-5" />} />
        <QuickAction index={2} href="/workspaces/observatory/timeline" label="Timeline" description="La chronologie du projet" icon={<Clock className="h-5 w-5" />} />
        <QuickAction index={3} href="/workspaces/observatory/search" label="Search" description="Recherche plein texte + RAG" icon={<Search className="h-5 w-5" />} />
      </div>

      {/* Activité récente */}
      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        <Panel index={0} title="Événements récents" icon={<Clock className="h-4 w-4" />} href="/workspaces/observatory/timeline">
          {recentEvents.length === 0 ? (
            <EmptyNote text="Aucun événement ingéré pour l'instant." />
          ) : (
            recentEvents.map((event, i) => (
              <div key={event.id} className="ethan-fade min-w-0 rounded-lg border border-line-1 bg-bg-1 px-3 py-2" style={staggerStyle(i, 20)}>
                <p className="truncate text-[13px] font-medium text-foreground">{event.content || event.type || event.id}</p>
                <p className="mt-0.5 text-[11px] text-foreground-tertiary">
                  {event.type || "event"} · {event.source || "webui"} · {formatDate(event.created_at)}
                </p>
              </div>
            ))
          )}
        </Panel>

        <Panel index={1} title="Facts mémoire récents" icon={<Database className="h-4 w-4" />} href="/workspaces/observatory/vault">
          {recentFacts.length === 0 ? (
            <EmptyNote text="Aucun fact actif en mémoire." />
          ) : (
            recentFacts.map((fact, i) => (
              <div key={fact.id} className="ethan-fade min-w-0 rounded-lg border border-line-1 bg-bg-1 px-3 py-2" style={staggerStyle(i, 20)}>
                <p className="truncate text-[13px] font-medium text-foreground">
                  <span className="text-foreground-secondary">{fact.subject}</span>
                  {" "}{fact.predicate}{" "}{fact.object}
                </p>
                <p className="mt-0.5 text-[11px] text-foreground-tertiary">
                  {fact.category ?? "uncategorized"} · confiance {Math.round((fact.confidence ?? 0) * 100)}%
                </p>
              </div>
            ))
          )}
        </Panel>

        <Panel index={2} title="Collections knowledge" icon={<Layers className="h-4 w-4" />} href="/knowledge">
          {recentCollections.length === 0 ? (
            <EmptyNote text="Aucune collection. Créez-en une depuis Knowledge." />
          ) : (
            recentCollections.map((collection, i) => (
              <div key={collection.id} className="ethan-fade min-w-0 rounded-lg border border-line-1 bg-bg-1 px-3 py-2" style={staggerStyle(i, 20)}>
                <p className="truncate text-[13px] font-medium text-foreground">{collection.name}</p>
                <p className="mt-0.5 text-[11px] text-foreground-tertiary">
                  {collection.document_ids?.length ?? 0} document(s){collection.parent_id ? " · sous-collection" : ""}
                </p>
              </div>
            ))
          )}
        </Panel>
      </div>

      {/* Points d'entrée directs vers les sections profondes */}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <Link
          href="/workspaces/observatory/engineering"
          className="group flex items-center gap-3 rounded-xl border border-line-1 bg-bg-1 p-4 transition-colors hover:border-primary/40 hover:bg-bg-2"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Boxes className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-foreground group-hover:text-primary">Engineering</p>
            <p className="truncate text-xs text-foreground-tertiary">ADR · ESR · composants · incidents · dépendances · dette</p>
          </div>
          <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-foreground-tertiary transition-transform group-hover:translate-x-0.5" />
        </Link>

        <Link
          href="/workspaces/observatory/ai-insights"
          className="group flex items-center gap-3 rounded-xl border border-line-1 bg-bg-1 p-4 transition-colors hover:border-primary/40 hover:bg-bg-2"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Bot className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-foreground group-hover:text-primary">AI Insights</p>
            <p className="truncate text-xs text-foreground-tertiary">Synthèses d&apos;agents distinguées des documents vérifiés</p>
          </div>
          <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-foreground-tertiary transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>
    </div>
  );
}

function StatTile({
  index,
  label,
  value,
  caption,
  icon,
  loading,
}: {
  index: number;
  label: string;
  value: number;
  caption: string;
  icon: React.ReactNode;
  loading?: boolean;
}) {
  return (
    <Card className="ethan-reveal p-4" style={staggerStyle(index, 32)}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground-tertiary">{label}</p>
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 text-primary">{icon}</div>
      </div>
      <p className="mt-1.5 text-2xl font-bold leading-none text-foreground">
        {/* Le compteur arrive après la requête : on fait apparaître la valeur
            réelle, jamais un chiffre provisoire. */}
        <span key={loading ? "loading" : String(value)} className="ethan-fade inline-block">
          {loading ? "…" : value}
        </span>
      </p>
      <p className="mt-1 text-[10px] text-foreground-tertiary">{caption}</p>
    </Card>
  );
}

function QuickAction({
  index,
  href,
  label,
  description,
  icon,
}: {
  index: number;
  href: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Link href={href} className="group">
      <Card className="ethan-reveal flex h-full items-center gap-3 p-4 transition-colors hover:border-primary/40 hover:bg-primary/5" style={staggerStyle(index, 32)}>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary/20">
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-foreground transition-colors group-hover:text-primary">{label}</p>
          <p className="mt-0.5 text-[11px] text-foreground-tertiary">{description}</p>
        </div>
      </Card>
    </Link>
  );
}

function Panel({
  index,
  title,
  icon,
  href,
  children,
}: {
  index: number;
  title: string;
  icon: React.ReactNode;
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="ethan-reveal flex flex-col p-4" style={staggerStyle(index, 40)}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-foreground-secondary">
          <span className="text-primary">{icon}</span>
          <h2 className="text-[13px] font-semibold uppercase tracking-wider">{title}</h2>
        </div>
        <Link href={href} className="text-[11px] font-medium text-primary hover:underline">
          Voir tout
        </Link>
      </div>
      <div className="flex flex-col gap-1.5">{children}</div>
    </Card>
  );
}

function EmptyNote({ text }: { text: string }) {
  return <p className="rounded-lg border border-dashed border-line-2 px-3 py-6 text-center text-xs text-foreground-tertiary">{text}</p>;
}

function formatDate(iso: string | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
}
