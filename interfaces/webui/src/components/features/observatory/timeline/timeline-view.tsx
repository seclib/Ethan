"use client";

/**
 * Observatory — Timeline (chronologie technique d'ETHAN).
 *
 * Fusionne deux sources réelles, marquées avec leur provenance :
 *  - Engineering Memory (enregistrements EVT/DEC/INC…, GET /v1/memory/records)
 *  - Memory Events du WebUI (GET /v1/memory/events — flux d'ingestion)
 * Les entrées sont triées par date décroissante, groupées par mois.
 * Chaque entrée pointant vers un document du vault devient un lien
 * cliquable ; celles-ci n'inventent jamais de source.
 */

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Clock, GitBranch, Terminal, FileText, Filter } from "lucide-react";
import { listEngineeringRecords, type EngineeringRecord } from "@/lib/api/observatory";
import { listMemoryEvents } from "@/lib/api/memory";

interface TimelineItem {
	id: string;
	date: Date;
	kind: string;
	label: string;
	detail: string;
	source: string;
	provenance: string;
	vaultPath: string | null;
}

const KIND_FILTERS = ["engineering", "memory"] as const;

function recordToItem(record: EngineeringRecord): TimelineItem {
	const source = record.source_of_fact ?? "";
	const vaultPathCandidate = extractVaultPath(source);
	return {
		id: `em-${record.id}`,
		date: parseDate(record.created_at),
		kind: "engineering",
		label: record.title || record.id,
		detail: `${record.record_type} · ${record.status}${record.components?.length ? " · " + record.components.join(", ") : ""}`,
		source,
		provenance: record.provenance_level ?? "unknown",
		vaultPath: vaultPathCandidate,
	};
}

function parseDate(value: string | undefined): Date {
	const date = value ? new Date(value) : new Date(0);
	return Number.isNaN(date.getTime()) ? new Date(0) : date;
}

function extractVaultPath(source: string): string | null {
	// Convention : les sources documentaires pointent vers un chemin du vault.
	// On accepte les chemins absolus connus et les chemins relatifs existants.
	if (!source) return null;
	const absolute = source.match(/(?:Obsidian\/)(.+?\.(?:md|json|csv|yaml|yml|ndjson|txt))/i);
	if (absolute) return absolute[1];
	const relative = source.match(/^[\w./-]+\.(?:md|json|csv|yaml|yml|ndjson|txt)$/i);
	return relative ? relative[0] : null;
}

export function TimelineView() {
	const [filter, setFilter] = React.useState<"all" | (typeof KIND_FILTERS)[number]>("all");

	const { data: records = [], isLoading: recordsLoading, isError: recordsError, error: recordsErrorObj } = useQuery({
		queryKey: ["timeline-engineering-records"],
		queryFn: () => listEngineeringRecords({ limit: 500 }),
		staleTime: 60_000,
	});
	const { data: events = [], isLoading: eventsLoading, isError: eventsError, error: eventsErrorObj } = useQuery({
		queryKey: ["timeline-memory-events"],
		queryFn: () => listMemoryEvents(),
		staleTime: 60_000,
	});

	const items = React.useMemo<TimelineItem[]>(() => {
		const engineering = records.map(recordToItem);
		const memory = events.map((event) => ({
			id: `webui-${event.id}`,
			date: parseDate(event.created_at),
			kind: "memory" as const,
			label: event.content || event.type || event.id,
			detail: `${event.type ?? "event"} · provenance: déclarée par l'interface`,
			source: event.source ?? "webui",
			provenance: "derived",
			vaultPath: null,
		}));
		return [...engineering, ...memory].sort((a, b) => b.date.getTime() - a.date.getTime());
	}, [records, events]);

	const filtered = React.useMemo(
		() => (filter === "all" ? items : items.filter((item) => item.kind === filter)),
		[items, filter],
	);

	const groups = React.useMemo(() => {
		const map = new Map<string, TimelineItem[]>();
		for (const item of filtered) {
			const key = item.date.toLocaleDateString(undefined, { year: "numeric", month: "long" });
			const bucket = map.get(key) ?? [];
			bucket.push(item);
			map.set(key, bucket);
		}
		return Array.from(map.entries());
	}, [filtered]);

	const loading = recordsLoading || eventsLoading;

	return (
		<div className="flex h-full min-h-0 flex-col bg-bg-1">
			<div className="flex flex-wrap items-center gap-2 border-b border-line-1 px-4 py-2">
				<div className="flex items-center gap-2 text-foreground-secondary">
					<Clock className="h-4 w-4 text-primary" />
					<span className="text-xs font-semibold uppercase tracking-wider">Chronologie</span>
					<span className="rounded bg-bg-2 px-1.5 py-0.5 text-[10px] text-foreground-tertiary">{filtered.length} entrées</span>
				</div>
				<div className="ml-auto flex items-center gap-1.5">
					<Filter className="h-3.5 w-3.5 text-foreground-tertiary" aria-hidden />
					{([
						["all", "Tout"],
						["engineering", "Engineering Memory"],
						["memory", "Mémoire WebUI"],
					] as const).map(([value, label]) => (
						<button
							key={value}
							type="button"
							onClick={() => setFilter(value)}
							aria-pressed={filter === value}
							className={`rounded-full border px-2.5 py-1 text-[10px] font-medium transition-colors ${
								filter === value ? "border-primary/50 bg-primary/15 text-primary" : "border-line-1 bg-bg-2 text-foreground-secondary hover:text-foreground"
							}`}
						>
							{label}
						</button>
					))}
				</div>
			</div>

			<div className="min-h-0 flex-1 overflow-y-auto p-5">
				{(recordsError || eventsError) && (
					<p className="mb-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-300">
						Historique partiellement indisponible — {recordsError ? String((recordsErrorObj as Error)?.message ?? recordsErrorObj) : ""}
						{recordsError && eventsError ? " · " : ""}
						{eventsError ? String((eventsErrorObj as Error)?.message ?? eventsErrorObj) : ""}
					</p>
				)}
				{loading && <p className="py-10 text-center text-xs text-foreground-tertiary">Chargement de l&apos;historique…</p>}
				{!loading && filtered.length === 0 && (
					<p className="mx-auto max-w-md py-16 text-center text-xs text-foreground-tertiary">
						Aucun événement enregistré pour ce filtre. La timeline se remplit à mesure que le
						runtime documente ses activités (Engineering Memory) et que l&apos;interface ingère
						des événements.
					</p>
				)}
				{groups.map(([month, groupItems]) => (
					<section key={month} className="relative mb-6 pl-6">
						<h2 className="mb-2 -ml-6 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.2em] text-foreground-tertiary">
							<span className="inline-block h-2 w-2 rounded-full bg-primary/70" /> {month}
						</h2>
						<div className="absolute left-[3px] top-5 h-full w-px bg-line-1" aria-hidden />
						<ol className="space-y-2">
							{groupItems.map((item) => (
								<li key={item.id} className="relative rounded-lg border border-line-1 bg-bg-2 p-3">
									<span className="absolute -left-[21px] top-4 h-2 w-2 rounded-full border border-bg-1 bg-foreground-tertiary" aria-hidden />
									<div className="flex flex-wrap items-center gap-2">
										{item.kind === "engineering" ? (
											<GitBranch className="h-3.5 w-3.5 shrink-0 text-primary" aria-hidden />
										) : (
											<Terminal className="h-3.5 w-3.5 shrink-0 text-emerald-400" aria-hidden />
										)}
										<p className="min-w-0 flex-1 truncate text-[12.5px] font-medium text-foreground" title={item.label}>{item.label}</p>
										<time className="shrink-0 font-mono text-[10px] text-foreground-tertiary" dateTime={item.date.toISOString()}>
											{item.date.toLocaleDateString(undefined, { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
										</time>
									</div>
									<p className="mt-1 truncate text-[10.5px] text-foreground-tertiary" title={item.detail}>{item.detail}</p>
									<div className="mt-1.5 flex flex-wrap items-center gap-2 text-[9.5px]">
										<span className="rounded border border-line-1 bg-bg-1 px-1.5 py-0.5 font-mono text-foreground-tertiary" title={`provenance: ${item.provenance}`}>
											{item.provenance}
										</span>
										<span className="max-w-[28rem] truncate text-foreground-tertiary" title={item.source}>{item.source}</span>
										{item.vaultPath && (
											<Link
												href={`/workspaces/observatory/vault?path=${encodeURIComponent(item.vaultPath)}`}
												className="ml-auto inline-flex shrink-0 items-center gap-1 font-medium text-primary hover:underline"
											>
												<FileText className="h-3 w-3" /> Source
											</Link>
										)}
									</div>
								</li>
							))}
						</ol>
					</section>
				))}
			</div>
		</div>
	);
}
