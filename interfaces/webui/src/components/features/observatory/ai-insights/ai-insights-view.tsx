"use client";

/**
 * Observatory — AI Insights (analyses et synthèses produites par les agents).
 *
 * Distinction de provenance non négociable :
 *  - « Synthèses d'agents » : documents du vault produits par un agent,
 *    jamais promus au rang de fait vérifié sans relecture humaine.
 *  - « Rapports agent (RPT-*) » : enregistrements Engineering Memory avec
 *    statut de provenance explicite (PROVISIONAL → REVIEWED → VALIDATED).
 * Les documents originaux (archives) restent accessibles ailleurs et ne sont
 * jamais renommés ici.
 */

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Sparkles, FileText, Bot, ShieldAlert, ChevronRight, Inbox, FlaskConical } from "lucide-react";
import { cn } from "@/lib/utils";
import { listEngineeringRecords, listVaultTree, type EngineeringRecord, type VaultNode } from "@/lib/api/observatory";

const SYNTHESIS_PREFIX = "Knowledge/Syntheses/by-agent";

function flattenPrefix(node: VaultNode, prefix: string): VaultNode[] {
	const out: VaultNode[] = [];
	const walk = (n: VaultNode) => {
		if (n.type === "file") {
			if (n.path.startsWith(prefix + "/")) out.push(n);
			return;
		}
		for (const child of n.children ?? []) walk(child);
	};
	walk(node);
	return out.sort((a, b) => a.path.localeCompare(b.path));
}

export function AiInsightsView() {
	const { data: tree, isError: treeError, error: treeErrorObj } = useQuery({ queryKey: ["vault-tree-ai"], queryFn: () => listVaultTree(), staleTime: 5 * 60_000 });

	const synthesisFiles = React.useMemo(
		() => (tree ? flattenPrefix(tree, SYNTHESIS_PREFIX) : []),
		[tree],
	);

	const { data: reports = [], isLoading, isError: reportsError, error: reportsErrorObj } = useQuery({
		queryKey: ["agent-reports"],
		queryFn: () => listEngineeringRecords({ record_type: "agent_report", limit: 100 }),
		staleTime: 60_000,
	});

	return (
		<div className="flex h-full min-h-0 flex-col bg-bg-1">
			<div className="border-b border-line-1 px-5 py-3">
				<h1 className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em] text-foreground-secondary">
					<Sparkles className="h-4 w-4 text-primary" /> AI Insights
				</h1>
				<p className="mt-1 flex items-start gap-1.5 text-[11px] leading-relaxed text-foreground-tertiary">
					<ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" aria-hidden />
					Les contenus ci-dessous sont des productions d&apos;agents : ils sont utiles pour la
					navigation, jamais comme preuve indépendante. Seuls les documents ORIGINAUX
					(archives, ADR/ESR) font foi.
				</p>
			</div>

			<div className="min-h-0 flex-1 overflow-y-auto p-5">
				{treeError && (
					<p className="mb-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-[11px] text-red-300">
						Arborescence du vault indisponible : {String((treeErrorObj as Error)?.message ?? treeErrorObj)}
					</p>
				)}
				<SectionTitle icon={<Bot className="h-4 w-4" />} title="Synthèses d'agents (vault)" count={synthesisFiles.length} />
				<p className="mb-3 mt-0.5 text-[11px] text-foreground-tertiary">
					Fichiers générés sous <code className="rounded bg-bg-2 px-1 font-mono text-[10px]">{SYNTHESIS_PREFIX}/</code>.
					Versions horodatées préservées — les versions canoniques sont celles post-synchronisation.
				</p>
				{synthesisFiles.length === 0 ? (
					<EmptyState text="Aucune synthèse d'agent dans le vault. Les archives existent mais aucune synthèse n'est indexée ici." />
				) : (
					<ul className="grid gap-1.5 md:grid-cols-2">
						{synthesisFiles.map((file) => (
							<li key={file.path}>
								<Link
									href={`/workspaces/observatory/vault?path=${encodeURIComponent(file.path)}`}
									className="group flex items-start gap-2.5 rounded-lg border border-line-1 bg-bg-2 p-3 transition-colors hover:border-primary/40"
								>
									<FileText className="mt-0.5 h-4 w-4 shrink-0 text-foreground-tertiary group-hover:text-primary" />
									<span className="min-w-0">
										<span className="block truncate text-[12px] font-medium text-foreground">{file.name}</span>
										<span className="mt-1 inline-flex items-center gap-1 rounded border border-amber-500/30 bg-amber-500/10 px-1.5 py-0.5 text-[9px] font-medium text-amber-300">
											synthèse agent · non vérifiée
										</span>
										<span className="mt-1 block truncate font-mono text-[9px] text-foreground-tertiary">{file.path}</span>
									</span>
									<ChevronRight className="ml-auto mt-1 h-3.5 w-3.5 shrink-0 text-foreground-tertiary transition-transform group-hover:translate-x-0.5" />
								</Link>
							</li>
						))}
					</ul>
				)}

				<div className="mt-6">
					<SectionTitle icon={<FlaskConical className="h-4 w-4" />} title="Rapports d'agents Engineering Memory (RPT-*)" count={reports.length} />
					<p className="mb-3 mt-0.5 text-[11px] text-foreground-tertiary">
						Enregistrements <code className="rounded bg-bg-2 px-1 font-mono text-[10px]">agent_report</code> avec statut de
						provenance explicite : PROVISIONAL → REVIEWED → VALIDATED. La promotion requiert une relecture humaine.
					</p>
					{reportsError && (
						<p className="mb-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-300">
							Rapports Engineering Memory indisponibles : {String((reportsErrorObj as Error)?.message ?? reportsErrorObj)}
						</p>
					)}
					{isLoading && <p className="py-6 text-center text-xs text-foreground-tertiary">Chargement…</p>}
					{!isLoading && reports.length === 0 && (
						<div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-line-2 px-4 py-8 text-center">
							<Inbox className="h-6 w-6 text-foreground-tertiary" aria-hidden />
							<p className="max-w-md text-[11px] leading-relaxed text-foreground-tertiary">
								Aucun rapport d&apos;agent RPT-* enregistré dans l&apos;Engineering Memory. Les rapports d&apos;agents
								(audits, diagnostics) apparaîtront ici dès qu&apos;ils transitent par le service Engineering Memory —
								avec provenance et statut de relecture explicites.
							</p>
						</div>
					)}
					{reports.length > 0 && (
						<ul className="grid gap-1.5 md:grid-cols-2">
							{reports.map((record) => (
								<li key={record.id} className="rounded-lg border border-line-1 bg-bg-2 p-3">
									<div className="flex items-center gap-2">
										<span className={cn(
											"rounded border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide",
											record.status === "VALIDATED"
												? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
												: record.status === "REVIEWED"
													? "border-sky-500/40 bg-sky-500/10 text-sky-300"
													: "border-amber-500/40 bg-amber-500/10 text-amber-300",
										)}>
											{record.status}
										</span>
										<time className="font-mono text-[9.5px] text-foreground-tertiary" dateTime={record.created_at}>
											{new Date(record.created_at).toLocaleDateString(undefined, { dateStyle: "short" })}
										</time>
									</div>
									<p className="mt-1.5 text-[12px] font-medium leading-snug text-foreground">{record.title || record.id}</p>
									{record.authors?.length > 0 && (
										<p className="mt-0.5 font-mono text-[9px] text-foreground-tertiary">agent(s): {record.authors.join(", ")}</p>
									)}
								</li>
							))}
						</ul>
					)}
				</div>

				<div className="mt-6 rounded-lg border border-line-1 bg-bg-2 p-4 text-[11px] leading-relaxed text-foreground-tertiary">
					<p className="font-semibold text-foreground-secondary">Où sont les preuves originales ?</p>
					<p className="mt-1">
						Les archives brutes (Archives/) et les documents de référence (Knowledge/, Architecture/)
						resterent la source de vérité documentaire. Les synthèses d&apos;agents ne remplacent jamais
						ces originaux — elles les référencent. Toute promotion au statut de décision requiert une
						relecture humaine et, pour l&apos;Engineering Memory, le passage PROVISIONAL → REVIEWED → VALIDATED.
					</p>
				</div>
			</div>
		</div>
	);
}

function SectionTitle({ icon, title, count }: { icon: React.ReactNode; title: string; count: number }) {
	return (
		<h2 className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-foreground-secondary">
			<span className="text-primary">{icon}</span> {title}
			<span className="rounded bg-bg-2 px-1.5 py-0.5 text-[10px] text-foreground-tertiary">{count}</span>
		</h2>
	);
}

function EmptyState({ text }: { text: string }) {
	return <p className="rounded-lg border border-dashed border-line-2 px-4 py-6 text-center text-[11px] text-foreground-tertiary">{text}</p>;
}
