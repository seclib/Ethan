"use client";

/**
 * Observatory — Engineering (connaissances d'ingénierie organisées).
 *
 * Trois familles de sources réelles, jamais fusionnées artificiellement :
 *  - Documents ADR / ESR / ASR / Archives : fichiers du vault
 *    (l'arborescence vient de GET /v1/memory/vault/tree — organisation d'origine).
 *  - Enregistrements Engineering Memory (composants, incidents, dépendances,
 *    tests, dette) : GET /v1/memory/records.
 *  - État du vault : GET /v1/memory/health.
 */

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
	FileText,
	ScrollText,
	ShieldCheck,
	Boxes,
	LifeBuoy,
	Package,
	FlaskConical,
	Receipt,
	Archive,
	ChevronRight,
	Database,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
	listEngineeringRecords,
	listVaultTree,
	getMemoryIntegrity,
	type EngineeringRecord,
	type VaultNode,
} from "@/lib/api/observatory";

type EngineeringTab =
	| "adr" | "esr" | "asr" | "components" | "incidents"
	| "dependencies" | "tests" | "debt" | "archives";

const TABS: Array<{ id: EngineeringTab; label: string; icon: React.ComponentType<{ className?: string }> }> = [
	{ id: "adr", label: "ADR", icon: ScrollText },
	{ id: "esr", label: "ESR", icon: FileText },
	{ id: "asr", label: "ASR", icon: ShieldCheck },
	{ id: "components", label: "Composants", icon: Boxes },
	{ id: "incidents", label: "Incidents", icon: LifeBuoy },
	{ id: "dependencies", label: "Dépendances", icon: Package },
	{ id: "tests", label: "Tests & preuves", icon: FlaskConical },
	{ id: "debt", label: "Dette technique", icon: Receipt },
	{ id: "archives", label: "Archives", icon: Archive },
];

const VAULT_PREFIXES: Partial<Record<EngineeringTab, string[]>> = {
	adr: ["Architecture/ADR"],
	esr: ["Architecture/ESR"],
	asr: ["Architecture/ASR"],
};

const RECORD_TYPES: Partial<Record<EngineeringTab, string>> = {
	components: "component",
	incidents: "incident",
	dependencies: "dependency",
	tests: "test_result",
	debt: "technical_debt",
};

function flattenFiles(node: VaultNode, prefix: string): VaultNode[] {
	const out: VaultNode[] = [];
	const walk = (n: VaultNode) => {
		if (n.type === "file") {
			if (n.path.startsWith(prefix + "/") || n.path.startsWith(prefix + "_") || n.path.startsWith(prefix)) {
				out.push(n);
			}
			return;
		}
		for (const child of n.children ?? []) walk(child);
	};
	walk(node);
	return out.sort((a, b) => a.path.localeCompare(b.path));
}

export function EngineeringView() {
	const [tab, setTab] = React.useState<EngineeringTab>("adr");
	const { data: tree, isError: treeError, error: treeErrorObj } = useQuery({ queryKey: ["vault-tree-eng"], queryFn: () => listVaultTree(), staleTime: 5 * 60_000 });
	const { data: integrity } = useQuery({ queryKey: ["memory-integrity"], queryFn: () => getMemoryIntegrity(), staleTime: 60_000 });

	const vaultPrefix = VAULT_PREFIXES[tab]?.[0];
	const recordType = RECORD_TYPES[tab];

	const vaultFiles = React.useMemo(
		() => (tree && vaultPrefix ? flattenFiles(tree, vaultPrefix) : []),
		[tree, vaultPrefix],
	);

	const { data: records = [], isLoading: recordsLoading } = useQuery({
		queryKey: ["engineering-records", recordType],
		queryFn: () => listEngineeringRecords({ record_type: recordType as string, limit: 100 }),
		enabled: !!recordType,
		staleTime: 60_000,
	});

	const archiveEntries = React.useMemo(
		() => (tab === "archives" && tree ? collectLevel(tree, "Archives") : []),
		[tab, tree],
	);

	return (
		<div className="flex h-full min-h-0 flex-col bg-bg-1">
			<div className="flex flex-wrap items-center gap-2 border-b border-line-1 px-4 py-2">
				<div className="flex items-center gap-2 text-foreground-secondary">
					<Database className="h-4 w-4 text-primary" />
					<span className="text-xs font-semibold uppercase tracking-wider">Engineering</span>
					{integrity && (
						<span className="rounded border border-line-1 bg-bg-2 px-2 py-0.5 text-[10px] text-foreground-tertiary" title="Intégrité de l'Engineering Memory (Obsidian)">
							{integrity.valid_records}/{integrity.markdown_files} documents valides
						</span>
					)}
				</div>
				<nav className="flex gap-1 overflow-x-auto" aria-label="Catégories d'ingénierie">
					{TABS.map(({ id, label, icon: Icon }) => (
						<button
							key={id}
							type="button"
							role="tab"
							aria-selected={tab === id}
							onClick={() => setTab(id)}
							className={cn(
								"flex items-center gap-1.5 whitespace-nowrap rounded-md px-2.5 py-1.5 text-[11px] font-medium transition-colors",
								tab === id ? "bg-primary/15 text-primary" : "text-foreground-secondary hover:bg-bg-2",
							)}
						>
							<Icon className="h-3.5 w-3.5" /> {label}
						</button>
					))}
				</nav>
			</div>

			<div className="min-h-0 flex-1 overflow-y-auto p-5">
				{treeError && (
					<p className="mb-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-[11px] text-red-300">
						Arborescence du vault indisponible : {String((treeErrorObj as Error)?.message ?? treeErrorObj)}
					</p>
				)}
				{vaultPrefix && (
					<FileList tab={tab} files={vaultFiles} />
				)}

				{tab === "archives" && (
					<ArchiveList entries={archiveEntries} />
				)}

				{recordType && (
					<RecordList records={records} loading={recordsLoading} emptyHint={emptyHintFor(tab)} />
				)}
			</div>
		</div>
	);
}

function FileList({ tab, files }: { tab: EngineeringTab; files: VaultNode[] }) {
	if (files.length === 0) {
		return <EmptyBox>Aucun document {tab.toUpperCase()} dans le vault ({"Architecture/" + tab.toUpperCase()}).</EmptyBox>;
	}
	return (
		<ul className="grid gap-1.5 md:grid-cols-2">
			{files.map((file) => (
				<li key={file.path}>
					<Link
						href={`/workspaces/observatory/vault?path=${encodeURIComponent(file.path)}`}
						className="group flex items-start gap-2.5 rounded-lg border border-line-1 bg-bg-2 p-3 transition-colors hover:border-primary/40"
					>
						<FileText className="mt-0.5 h-4 w-4 shrink-0 text-foreground-tertiary group-hover:text-primary" />
						<span className="min-w-0">
							<span className="block truncate text-[12px] font-medium text-foreground">{file.name}</span>
							<span className="mt-0.5 block truncate font-mono text-[9.5px] text-foreground-tertiary">{file.path}</span>
						</span>
						<ChevronRight className="ml-auto mt-1 h-3.5 w-3.5 shrink-0 text-foreground-tertiary transition-transform group-hover:translate-x-0.5" />
					</Link>
				</li>
			))}
		</ul>
	);
}

function ArchiveList({ entries }: { entries: VaultNode[] }) {
	if (entries.length === 0) return <EmptyBox>Archives indisponibles ou vides.</EmptyBox>;
	const totalBytes = entries.reduce((sum, n) => sum + (n.size_bytes ?? 0), 0);
	return (
		<div>
			<p className="mb-3 max-w-xl text-[11px] leading-relaxed text-foreground-tertiary">
				Les archives brutes sont <strong className="text-foreground">immutables depuis l&apos;interface</strong> :
				le Core refuse toute écriture sous Archives/. Elles conservent la valeur de preuve historique.
			</p>
			<ul className="grid gap-1.5 md:grid-cols-2">
				{entries.map((entry) =>
					entry.type === "file" ? (
						<li key={entry.path}>
							<Link
								href={`/workspaces/observatory/vault?path=${encodeURIComponent(entry.path)}`}
								className="group flex items-center gap-2.5 rounded-lg border border-line-1 bg-bg-2 p-3 transition-colors hover:border-primary/40"
							>
								<Archive className="h-4 w-4 shrink-0 text-foreground-tertiary group-hover:text-primary" />
								<span className="min-w-0">
									<span className="block truncate text-[12px] font-medium text-foreground">{entry.name}</span>
									<span className="mt-0.5 block font-mono text-[9.5px] text-foreground-tertiary">{((entry.size_bytes ?? 0) / 1024).toFixed(0)} Ko · fichier archivé</span>
								</span>
								<ChevronRight className="ml-auto h-3.5 w-3.5 shrink-0 text-foreground-tertiary" />
							</Link>
						</li>
					) : (
						<li key={entry.path}>
							<div className="flex items-center gap-2.5 rounded-lg border border-line-1 bg-bg-2 p-3">
								<Archive className="h-4 w-4 shrink-0 text-foreground-tertiary" />
								<span className="min-w-0">
									<span className="block truncate text-[12px] font-medium text-foreground">{entry.name}</span>
									<span className="mt-0.5 block font-mono text-[9.5px] text-foreground-tertiary">{entry.children?.length ?? 0} entrées · dossier archivé</span>
								</span>
							</div>
						</li>
					),
				)}
			</ul>
			<p className="mt-3 text-[10px] text-foreground-tertiary">{entries.length} entrées · {(totalBytes / (1024 * 1024)).toFixed(1)} Mo (dossiers comptés pour 0 octet)</p>
		</div>
	);
}

function RecordList({ records, loading, emptyHint }: { records: EngineeringRecord[]; loading: boolean; emptyHint: string }) {
	if (loading) return <p className="py-10 text-center text-xs text-foreground-tertiary">Chargement…</p>;
	if (records.length === 0) return <EmptyBox>{emptyHint}</EmptyBox>;
	return (
		<ul className="grid gap-1.5 md:grid-cols-2">
			{records.map((record) => (
				<li key={record.id} className="rounded-lg border border-line-1 bg-bg-2 p-3">
					<div className="flex flex-wrap items-center gap-2">
						<span className="rounded border border-line-1 bg-bg-1 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wide text-foreground-secondary">{record.status}</span>
						<span className="font-mono text-[9.5px] text-foreground-tertiary">{record.record_type}</span>
						<time className="ml-auto font-mono text-[9.5px] text-foreground-tertiary" dateTime={record.created_at}>
							{new Date(record.created_at).toLocaleDateString(undefined, { dateStyle: "short" })}
						</time>
					</div>
					<p className="mt-1.5 text-[12px] font-medium leading-snug text-foreground">{record.title || record.id}</p>
					{record.source_of_fact && (
						<p className="mt-1 truncate text-[10px] text-foreground-tertiary" title={record.source_of_fact}>
							source: {record.source_of_fact}
						</p>
					)}
					{record.components?.length > 0 && (
						<p className="mt-0.5 truncate text-[10px] text-foreground-tertiary" title={record.components.join(", ")}>
							{record.components.join(" · ")}
						</p>
					)}
				</li>
			))}
		</ul>
	);
}

function collectLevel(tree: VaultNode, prefix: string): VaultNode[] {
	function find(node: VaultNode): VaultNode | null {
		if (node.type === "directory" && (node.path === prefix || node.name === prefix)) return node;
		for (const child of node.children ?? []) {
			const hit = find(child);
			if (hit) return hit;
		}
		return null;
	}
	const archives = find(tree);
	return archives?.children ?? [];
}

function EmptyBox({ children }: { children: React.ReactNode }) {
	return <p className="mx-auto max-w-md py-14 text-center text-xs leading-relaxed text-foreground-tertiary">{children}</p>;
}

function emptyHintFor(tab: EngineeringTab): string {
	switch (tab) {
		case "components": return "Aucun composant enregistré dans l'Engineering Memory.";
		case "incidents": return "Aucun incident enregistré — la santé du runtime est suivie ailleurs (Diagnostics).";
		case "dependencies": return "Aucune dépendance enregistrée (schéma DEP-*).";
		case "tests": return "Aucun test enregistré via l'Engineering Memory (TST-*).";
		case "debt": return "Aucune dette technique enregistrée (DEBT-*).";
		default: return "Aucun enregistrement.";
	}
}
