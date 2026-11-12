'use client';

/**
 * Engineering Memory — interface d'exploitation pour la mémoire technique.
 *
 * Utilise exclusivement les APIs réelles exposées par ETHAN.
 * Les états vides, en erreur et de chargement sont affichés tels quels.
 */

import * as React from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

type MemoryHealth = {
	status?: string;
	valid_records?: number;
	total_records?: number;
	invalid_records?: Array<string>;
};

type MemoryEvent = {
	id: string;
	record_type?: string;
	title?: string;
	status?: string;
	origin?: string;
	source_of_fact?: string;
	authors?: string[];
	components?: string[];
	created_at?: string;
	notes?: string;
};

type KnowledgeNode = {
	id: string;
	label: string;
	node_type: string;
	source: string;
	updated_at?: string;
};

type Skill = {
	id: string;
	name: string;
	status?: string;
	version?: string;
	updated_at?: string;
};

type MemoryTab =
	| 'overview'
	| 'events'
	| 'knowledge'
	| 'skills'
	| 'decisions'
	| 'graph'
	| 'administration';

const TABS: { id: MemoryTab; label: string }[] = [
	{ id: 'overview', label: 'Vue d ensemble' },
	{ id: 'events', label: 'Événements' },
	{ id: 'knowledge', label: 'Knowledge' },
	{ id: 'skills', label: 'Skills' },
	{ id: 'decisions', label: 'Décisions' },
	{ id: 'graph', label: 'Graphe' },
	{ id: 'administration', label: 'Administration' },
];

async function fetchJson<T>(path: string): Promise<T> {
	const response = await fetch(path, { credentials: 'include' });
	if (!response.ok) {
		throw new Error(`HTTP ${response.status}: ${path}`);
	}
	return (await response.json()) as T;
}

export default function EngineeringMemoryPage() {
	const [activeTab, setActiveTab] = React.useState<MemoryTab>('overview');
	const [health, setHealth] = React.useState<MemoryHealth | null>(null);
	const [events, setEvents] = React.useState<MemoryEvent[]>([]);
	const [knowledge, setKnowledge] = React.useState<KnowledgeNode[]>([]);
	const [skills, setSkills] = React.useState<Skill[]>([]);
	const [loading, setLoading] = React.useState(true);
	const [error, setError] = React.useState<string | null>(null);
	const [filter, setFilter] = React.useState('');

	const loadOverview = React.useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const [healthData, eventsData] = await Promise.all([
				fetchJson<MemoryHealth>('/api/v1/memory/health'),
				fetchJson<{ results?: MemoryEvent[] }>('/api/v1/memory/events'),
			]);
			setHealth(healthData);
			setEvents(eventsData.results ?? []);
		} catch (fetchError) {
			setError(fetchError instanceof Error ? fetchError.message : 'Erreur inconnue');
		} finally {
			setLoading(false);
		}
	}, []);

	const loadKnowledge = React.useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await fetchJson<KnowledgeNode[]>('/api/v1/knowledge');
			setKnowledge(data);
		} catch (fetchError) {
			setError(fetchError instanceof Error ? fetchError.message : 'Erreur inconnue');
		} finally {
			setLoading(false);
		}
	}, []);

	const loadSkills = React.useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await fetchJson<Skill[]>('/api/v1/plugins');
			setSkills(data);
		} catch (fetchError) {
			setError(fetchError instanceof Error ? fetchError.message : 'Erreur inconnue');
		} finally {
			setLoading(false);
		}
	}, []);

	React.useEffect(() => {
		if (activeTab === 'overview' || activeTab === 'events') void loadOverview();
		else if (activeTab === 'knowledge') void loadKnowledge();
		else if (activeTab === 'skills') void loadSkills();
		else setLoading(false);
	}, [activeTab, loadOverview, loadKnowledge, loadSkills]);

	const visibleEvents = events.filter((event) =>
		!filter || event.title?.toLowerCase().includes(filter.toLowerCase()),
	);

	return (
		<div className="flex flex-col gap-6 p-6 text-sm text-foreground">
			<header className="flex flex-col gap-2">
				<h1 className="text-2xl font-semibold">Engineering Memory</h1>
				<p className="text-foreground-tertiary">
					Mémoire technique d ETHAN fondée sur les données réelles du service.
				</p>
			</header>

			<nav className="flex flex-wrap gap-2">
				{TABS.map((tab) => (
					<Button
						key={tab.id}
						variant={activeTab === tab.id ? 'primary' : 'secondary'}
						onClick={() => setActiveTab(tab.id)}
					>
						{tab.label}
					</Button>
				))}
			</nav>

			{loading && <p className="text-foreground-tertiary">Chargement des données réelles...</p>}

			{error && (
				<div className="rounded-md border border-red-700 bg-red-950 p-4 text-red-200">
					Erreur de récupération réelle : {error}
				</div>
			)}

			{activeTab === 'overview' && (
				<section className="grid gap-4 md:grid-cols-2">
					<Card title="État du service" lines={[
						`Statut : ${health?.status ?? 'inconnu'}`,
						`Enregistrements valides : ${health?.valid_records ?? 0}`,
						`Enregistrements totaux : ${health?.total_records ?? 0}`,
						`Enregistrements invalides : ${health?.invalid_records?.length ?? 0}`,
					]} />
					<Card title="Derniers événements" lines={events.slice(0, 5).map((item) => `${item.id} — ${item.title ?? 'sans titre'} — ${item.status ?? 'sans état'}`)} />
				</section>
			)}

			{activeTab === 'events' && (
				<section className="flex flex-col gap-4">
					<Input
						aria-label="Filtrer les événements par titre"
						value={filter}
						onChange={(event) => setFilter(event.target.value)}
						placeholder="Filtrer par titre"
					/>
					<div className="overflow-x-auto rounded-md border border-border">
						<table className="w-full text-left text-sm">
							<thead className="border-b border-border bg-elevated">
								<tr>
									<th className="px-3 py-2">Identifiant</th>
									<th className="px-3 py-2">Type</th>
									<th className="px-3 py-2">Titre</th>
									<th className="px-3 py-2">Statut</th>
									<th className="px-3 py-2">Source</th>
									<th className="px-3 py-2">Date</th>
								</tr>
							</thead>
							<tbody>
								{visibleEvents.map((event) => (
									<tr key={event.id} className="border-b border-border/50">
										<td className="px-3 py-2 font-mono">{event.id}</td>
										<td className="px-3 py-2">{event.record_type ?? 'non renseigné'}</td>
										<td className="px-3 py-2">{event.title ?? 'sans titre'}</td>
										<td className="px-3 py-2">
											<Badge>{event.status ?? 'non renseigné'}</Badge>
										</td>
										<td className="px-3 py-2">{event.source_of_fact ?? 'inconnu'}</td>
										<td className="px-3 py-2">{event.created_at ?? 'inconnu'}</td>
									</tr>
								))}
							</tbody>
						</table>
						{!loading && visibleEvents.length === 0 && (
							<p className="p-4 text-foreground-tertiary">Aucun événement ne correspond.</p>
						)}
					</div>
				</section>
			)}

			{activeTab === 'knowledge' && (
				<section className="flex flex-col gap-3">
					{knowledge.map((node) => (
						<div key={node.id} className="rounded-md border border-border p-3">
							<p className="font-medium">{node.label}</p>
							<p className="text-foreground-tertiary">{node.node_type} — {node.source}</p>
							<p className="text-foreground-tertiary">{node.updated_at ?? 'date inconnue'}</p>
						</div>
					))}
					{!loading && knowledge.length === 0 && <p className="text-foreground-tertiary">Aucune donnée Knowledge accessible.</p>}
				</section>
			)}

			{activeTab === 'skills' && (
				<section className="flex flex-col gap-3">
					{skills.map((skill) => (
						<div key={skill.id} className="rounded-md border border-border p-3">
							<p className="font-medium">{skill.name}</p>
							<p className="text-foreground-tertiary">{skill.status ?? 'statut inconnu'} — {skill.version ?? 'version inconnue'}</p>
							<p className="text-foreground-tertiary">{skill.updated_at ?? 'date inconnue'}</p>
						</div>
					))}
					{!loading && skills.length === 0 && <p className="text-foreground-tertiary">Aucune donnée Skill accessible.</p>}
				</section>
			)}

			{activeTab === 'decisions' && (
				<section className="rounded-md border border-border p-4">
					<p className="text-foreground-tertiary">
						Les ADR, ESR et ASR réels se consultent via les documents Obsidian. Cette interface ne génère aucune décision fictive.
					</p>
				</section>
			)}

			{activeTab === 'graph' && (
				<section className="rounded-md border border-border p-4">
					<p className="text-foreground-tertiary">
						Domaine en cours d implémentation. Les nœuds affichés seront toujours reconstruits depuis les événements et les relations enregistrées.
					</p>
					<p className="text-foreground-tertiary">
						Événements actuellement disponibles : {events.length}. Aucun graphique n&apos;est présenté comme complet.
					</p>
				</section>
			)}

			{activeTab === 'administration' && (
				<section className="flex flex-col gap-4">
					<Card title="État d intégrité" lines={[
						`Enregistrements valides : ${health?.valid_records ?? 0}`,
						`Enregistrements invalides : ${health?.invalid_records?.length ?? 0}`,
					]} />
					<Card title="Collecteurs et erreurs" lines={[
						error ?? 'Aucune erreur de collecte active',
					]} />
				</section>
			)}
		</div>
	);
}

function Card({ title, lines }: { title: string; lines: string[] }) {
	return (
		<div className="rounded-md border border-border p-4">
			<h2 className="mb-2 font-medium">{title}</h2>
			<ul className="space-y-1 text-foreground-tertiary">
				{lines.map((line) => (
					<li key={line}>{line}</li>
				))}
			</ul>
		</div>
	);
}

