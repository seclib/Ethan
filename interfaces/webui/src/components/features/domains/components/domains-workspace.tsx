"use client";

/**
 * DomainsWorkspace — vue des domaines de spécialité ETHAN.
 *
 * Gauche : liste des domains (création, suppression).  Droite : ressources
 * rattachées au domain sélectionné (résolues par le Core).  Toute la logique
 * (memberships many-to-many, résolution) appartient au Core via /v1/domains —
 * cette vue ne détient aucun état métier.
 */

import * as React from "react";
import { FolderTree, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import {
	listDomains,
	createDomain,
	deleteDomain,
	listDomainResources,
	type DomainWithCount,
	type DomainResource,
} from "@/lib/api/domains";

export function DomainsWorkspace() {
	const [domains, setDomains] = React.useState<DomainWithCount[] | null>(null);
	const [selectedId, setSelectedId] = React.useState<string | null>(null);
	const [resources, setResources] = React.useState<DomainResource[] | null>(null);
	const [newName, setNewName] = React.useState("");
	const [error, setError] = React.useState<string | null>(null);

	const reload = React.useCallback(async () => {
		try {
			const list = await listDomains();
			setDomains(list);
		} catch (e) {
			setError(e instanceof Error ? e.message : "Erreur de chargement");
		}
	}, []);

	React.useEffect(() => {
		void reload();
	}, [reload]);

	React.useEffect(() => {
		if (!selectedId) {
			setResources(null);
			return;
		}
		setResources(null);
		listDomainResources(selectedId)
			.then(setResources)
			.catch((e) => setError(e instanceof Error ? e.message : "Erreur"));
	}, [selectedId]);

	const handleCreate = async () => {
		const name = newName.trim();
		if (!name) return;
		setError(null);
		try {
			const domain = await createDomain({ name });
			setNewName("");
			await reload();
			setSelectedId(domain.id);
		} catch (e) {
			setError(e instanceof Error ? e.message : "Création impossible");
		}
	};

	const handleDelete = async (id: string) => {
		setError(null);
		try {
			await deleteDomain(id);
			if (selectedId === id) setSelectedId(null);
			await reload();
		} catch (e) {
			setError(e instanceof Error ? e.message : "Suppression impossible");
		}
	};

	if (domains === null) {
		return (
			<div className="flex h-full items-center justify-center">
				<Spinner />
			</div>
		);
	}

	return (
		<div className="flex h-full min-h-0">
			{/* Sidebar domains */}
			<aside className="flex w-72 flex-col gap-3 border-r p-4">
				<div className="flex items-center gap-2 text-sm font-semibold">
					<FolderTree className="size-4" /> Domaines
				</div>
				<div className="flex gap-2">
					<Input
						value={newName}
						onChange={(e) => setNewName(e.target.value)}
						onKeyDown={(e) => e.key === "Enter" && void handleCreate()}
						placeholder="Nouveau domaine…"
					/>
					<Button size="sm" onClick={() => void handleCreate()}>
						Créer
					</Button>
				</div>
				<nav className="min-h-0 flex-1 space-y-1 overflow-y-auto">
					{domains.map((d) => (
						<button
							key={d.id}
							type="button"
							onClick={() => setSelectedId(d.id)}
							className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm ${
								selectedId === d.id ? "bg-primary/10 font-medium" : "hover:bg-muted"
							}`}
						>
							<span className="truncate">{d.name}</span>
							<span className="flex items-center gap-2">
								<span className="text-xs text-muted-foreground">
									{d.resource_count}
								</span>
								<Trash2
									className="size-3.5 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
									onClick={(e) => {
										e.stopPropagation();
										void handleDelete(d.id);
									}}
								/>
							</span>
						</button>
					))}
					{domains.length === 0 && (
						<p className="px-3 py-6 text-center text-xs text-muted-foreground">
							Aucun domaine. Créez OSINT, Recon, Forensic…
						</p>
					)}
				</nav>
			</aside>

			{/* Ressources du domaine sélectionné */}
			<main className="min-h-0 flex-1 overflow-y-auto p-6">
				{error && <p className="mb-4 text-sm text-destructive">{error}</p>}
				{!selectedId ? (
					<p className="text-sm text-muted-foreground">
						Sélectionnez un domaine pour voir ses ressources.
					</p>
				) : resources === null ? (
					<Spinner />
				) : resources.length === 0 ? (
					<p className="text-sm text-muted-foreground">
						Aucune ressource rattachée à ce domaine.
					</p>
				) : (
					<ul className="space-y-2">
						{resources.map((r) => (
							<li
								key={`${r.resource_type}:${r.resource_id}`}
								className="flex items-center justify-between rounded-md border px-4 py-3 text-sm"
							>
								<span className="font-medium">
									{String(r.record?.name ?? r.resource_id)}
								</span>
								<span className="text-xs uppercase text-muted-foreground">
									{r.resource_type}
								</span>
							</li>
						))}
					</ul>
				)}
			</main>
		</div>
	);
}
