"use client";

/**
 * ModelsWorkspace — cockpit du catalogue de modèles d'ETHAN.
 *
 * MODÈLE vs PROVIDER :
 * - un PROVIDER est un service (connexion, endpoint, auth, activation,
 *   test, découverte) — page /providers ;
 * - un MODÈLE est une entrée du catalogue exposé par un provider
 *   (GET /models = découverts + fiches custom) — cette page.
 *
 * Fonctionnalités (exclusivement branchées sur ETHAN Core) :
 * - recherche globale + filtres : provider, capacités (valeurs RÉELLES du
 *   Core, jamais inventées), source (découvert/custom), disponibilité ;
 * - trois vues : Cartes, Liste, Table (colonnes triables) ;
 * - comparaison de 2–3 modèles, uniquement sur les métadonnées réellement
 *   présentes (aucun champ inventé) ;
 * - actions réelles : définir le modèle par défaut DU PROVIDER
 *   (PUT /providers/{id}), activer/désactiver une fiche custom
 *   (POST /models/{id}/toggle), créer/éditer un preset custom
 *   (POST/PUT /models).
 *
 * Aucune logique métier, aucun registre parallèle : le Core reste la source
 * de vérité (règle AGENTS.md).
 */

import * as React from "react";
import { useModels } from "@/components/features/providers/hooks/use-models";
import { useProviders } from "@/components/features/providers/hooks/use-providers";
import {
	ModelPresetDialog,
	type ModelPresetPayload,
} from "@/components/features/providers/components/model-preset-dialog";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import {
	buildModelComparison,
	comparisonValue,
	DEFAULT_MODEL_FILTERS,
	filterModelCatalog,
	isModelActivationEditable,
	modelAvailabilityLabel,
	sortModelCatalog,
	type ModelCatalogFilters,
	type ModelSortKey,
	type SortDirection,
} from "@/lib/llm/model-catalog";
import {
	capabilityLabel,
	capabilityVariant,
	uniqueModelCapabilities,
} from "@/lib/llm/capabilities";
import {
	createModel,
	toggleModel,
	updateModel,
	type ModelInfo,
} from "@/lib/api/models";
import type { Provider } from "@/lib/api/providers";
import { useUIStore } from "@/store/ui.store";
import { cn } from "@/lib/utils";
import {
	AlertCircle,
	ArrowDown,
	ArrowUp,
	Check,
	Database,
	GitCompare,
	LayoutGrid,
	List,
	LoaderCircle,
	Plus,
	RefreshCw,
	Search,
	Settings2,
	Star,
	Table2,
	X,
} from "lucide-react";

type ViewMode = "cards" | "list" | "table";

const VIEWS: { id: ViewMode; label: string; icon: React.ElementType }[] = [
	{ id: "cards", label: "Cartes", icon: LayoutGrid },
	{ id: "list", label: "Liste", icon: List },
	{ id: "table", label: "Table", icon: Table2 },
];

/** Clé stable d'un modèle dans le catalogue agrégé (provider + id). */
export function modelKey(model: ModelInfo): string {
	return `${model.provider}::${model.id}`;
}

export function ModelsWorkspace() {
	const {
		providers,
		providersLoading,
		providersError,
		models,
		modelsLoading,
		modelsError,
		refetchModels,
		pinned,
		pinModel,
		unpinModel,
		isPinned,
	} = useModels();
	const { updateProviderAsync } = useProviders();
	const addToast = useUIStore((s) => s.addToast);

	const [filters, setFilters] = React.useState<ModelCatalogFilters>(DEFAULT_MODEL_FILTERS);
	const [view, setView] = React.useState<ViewMode>("cards");
	const [sortKey, setSortKey] = React.useState<ModelSortKey>("name");
	const [sortDirection, setSortDirection] = React.useState<SortDirection>("asc");
	const [selectedModel, setSelectedModel] = React.useState<ModelInfo | null>(null);
	const [presetTarget, setPresetTarget] = React.useState<{
		model: ModelInfo | null;
		basedOn: ModelInfo | null;
	} | null>(null);
	const [compareSelection, setCompareSelection] = React.useState<string[]>([]);
	const [compareOpen, setCompareOpen] = React.useState(false);

	const isLoading = providersLoading || modelsLoading;
	const error = providersError || modelsError;

	/** Capacités proposées au filtrage : union réelle des métadonnées Core. */
	const capabilityOptions = React.useMemo(() => uniqueModelCapabilities(models), [models]);

	/** Providers présents dans le catalogue (id → libellé Core). */
	const providerOptions = React.useMemo(() => {
		const ids = Array.from(new Set(models.map((m) => m.provider).filter(Boolean))).sort();
		return ids.map((id) => {
			const provider = providers.find((p) => p.id === id);
			return { id, label: provider ? `${provider.name} (${id})` : id };
		});
	}, [models, providers]);

	const filteredModels = React.useMemo(
		() => filterModelCatalog(models, filters, (m) => isPinned(m.provider, m.id)),
		// `pinned` est une dépendance réelle (isPinned lit l'état épinglé).
		// eslint-disable-next-line react-hooks/exhaustive-deps
		[models, filters, pinned],
	);

	const displayedModels = React.useMemo(
		() =>
			view === "table"
				? sortModelCatalog(filteredModels, sortKey, sortDirection)
				: filteredModels,
		[filteredModels, view, sortKey, sortDirection],
	);

	const comparedModels = React.useMemo(
		() => models.filter((m) => compareSelection.includes(modelKey(m))),
		[models, compareSelection],
	);

	const providerOf = React.useCallback(
		(model: ModelInfo): Provider | null =>
			providers.find((p) => p.id === model.provider) ?? null,
		[providers],
	);

	const isProviderDefault = React.useCallback(
		(model: ModelInfo) => providerOf(model)?.default_model === model.model,
		[providerOf],
	);

	const setFilter = <K extends keyof ModelCatalogFilters>(
		key: K,
		value: ModelCatalogFilters[K],
	) => setFilters((prev) => ({ ...prev, [key]: value }));

	const toggleCapabilityFilter = (capability: string) => {
		setFilters((prev) => ({
			...prev,
			capabilities: prev.capabilities.includes(capability)
				? prev.capabilities.filter((c) => c !== capability)
				: [...prev.capabilities, capability],
		}));
	};

	const handlePin = (model: ModelInfo) => {
		if (isPinned(model.provider, model.id)) unpinModel(model.provider, model.id);
		else pinModel(model.provider, model.id);
	};

	const toggleCompareSelection = (model: ModelInfo) => {
		const key = modelKey(model);
		if (compareSelection.includes(key)) {
			setCompareSelection(compareSelection.filter((k) => k !== key));
			return;
		}
		if (compareSelection.length >= 3) {
			addToast({ type: "warning", message: "Comparaison limitée à 3 modèles." });
			return;
		}
		setCompareSelection([...compareSelection, key]);
	};


	/** Modèle par défaut du provider — action Core réelle (PUT /providers/{id}). */
	const handleSetDefault = async (model: ModelInfo) => {
		if (!providerOf(model)) {
			addToast({
				type: "warning",
				message:
					"Provider inconnu du Core pour ce modèle — impossible de définir un défaut.",
			});
			return;
		}
		try {
			await updateProviderAsync(model.provider, { default_model: model.model });
			addToast({
				type: "success",
				message: `Modèle par défaut : ${model.name} (${model.provider})`,
			});
		} catch {
			// useProviders affiche déjà le détail de l'erreur.
		}
	};

	/** Activation d'une fiche custom — action Core réelle (POST /models/{id}/toggle). */
	const handleToggleCustom = async (model: ModelInfo) => {
		try {
			await toggleModel(model.id);
			await refetchModels();
			addToast({ type: "success", message: `Fiche « ${model.name} » mise à jour.` });
		} catch (err) {
			addToast({
				type: "error",
				message: err instanceof Error ? err.message : "Échec de l'activation.",
			});
		}
	};

	const handlePresetSubmit = async (payload: ModelPresetPayload) => {
		try {
			if (presetTarget?.model) {
				await updateModel(presetTarget.model.id, { ...payload });
				addToast({ type: "success", message: `Preset « ${payload.name} » enregistré.` });
			} else {
				await createModel({ ...payload });
				addToast({ type: "success", message: `Preset « ${payload.name} » créé.` });
			}
			await refetchModels();
		} catch (err) {
			addToast({
				type: "error",
				message:
					err instanceof Error ? err.message : "Échec de l'enregistrement du preset.",
			});
		}
	};

	const toggleSort = (key: ModelSortKey) => {
		if (sortKey === key) {
			setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
		} else {
			setSortKey(key);
			setSortDirection("asc");
		}
	};

	return (
		<div className="flex h-full flex-col">
			<PageHeader
				title="Models"
				description="Catalogue ETHAN Core — modèles découverts auprès des providers et fiches custom."
				icon={<Database className="h-5 w-5" />}
				count={displayedModels.length}
				actions={
					<div className="flex items-center gap-2">
						<Button
							size="sm"
							variant="secondary"
							onClick={() =>
								setPresetTarget({ model: null, basedOn: selectedModel ?? null })
							}
							title="Créer une fiche modèle custom (preset) dans le Core"
						>
							<Plus className="h-4 w-4" /> Preset
						</Button>
						<Button
							size="sm"
							variant="secondary"
							disabled={compareSelection.length < 2}
							onClick={() => setCompareOpen(true)}
							title="Comparer les métadonnées réellement présentes"
						>
							<GitCompare className="h-4 w-4" /> Comparer ({compareSelection.length})
						</Button>
						<Button
							variant="ghost"
							size="sm"
							onClick={() => refetchModels()}
							disabled={isLoading}
							aria-label="Actualiser"
						>
							<RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
						</Button>
					</div>
				}
			/>


			{/* Toolbar — recherche globale + filtres réels + vues */}
			<div className="flex flex-wrap items-center gap-2 border-b border-line-1 px-4 py-2">
				<div className="relative min-w-[200px] max-w-md flex-1">
					<Search
						size={16}
						className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary"
					/>
					<input
						type="text"
						value={filters.query}
						onChange={(e) => setFilter("query", e.target.value)}
						placeholder="Rechercher un modèle (nom, provider, capacité)…"
						aria-label="Rechercher un modèle"
						className="w-full rounded-lg border border-line-1 bg-bg-1 py-1.5 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
					/>
				</div>

				<select
					aria-label="Filtrer par provider"
					className="rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 text-sm text-foreground"
					value={filters.providerId ?? ""}
					onChange={(e) => setFilter("providerId", e.target.value || null)}
				>
					<option value="">Tous les providers</option>
					{providerOptions.map((option) => (
						<option key={option.id} value={option.id}>
							{option.label}
						</option>
					))}
				</select>

				<select
					aria-label="Filtrer par source"
					className="rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 text-sm text-foreground"
					value={filters.source}
					onChange={(e) =>
						setFilter("source", e.target.value as ModelCatalogFilters["source"])
					}
				>
					<option value="all">Toutes sources</option>
					<option value="discovered">Découverts</option>
					<option value="custom">Fiches custom</option>
				</select>

				<select
					aria-label="Filtrer par disponibilité"
					className="rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 text-sm text-foreground"
					value={filters.availability}
					onChange={(e) =>
						setFilter(
							"availability",
							e.target.value as ModelCatalogFilters["availability"],
						)
					}
				>
					<option value="all">Tous états</option>
					<option value="available">Disponibles</option>
					<option value="unavailable">Indisponibles</option>
				</select>

				<Button
					size="sm"
					variant={filters.pinnedOnly ? "default" : "outline"}
					onClick={() => setFilter("pinnedOnly", !filters.pinnedOnly)}
					title="Afficher uniquement les modèles épinglés"
				>
					<Star className="h-4 w-4" /> Favoris
				</Button>

				<div className="ml-auto flex items-center gap-1 rounded-lg border border-line-1 p-0.5">
					{VIEWS.map(({ id, label, icon: Icon }) => (
						<button
							key={id}
							type="button"
							onClick={() => setView(id)}
							aria-label={`Vue ${label}`}
							aria-pressed={view === id}
							title={label}
							className={cn(
								"rounded-md px-2 py-1.5 text-foreground-tertiary transition-colors",
								view === id ? "bg-accent/15 text-accent" : "hover:bg-bg-2",
							)}
						>
							<Icon className="h-4 w-4" />
						</button>
					))}
				</div>
			</div>

			{/* Capacités réelles du Core — filtres construits sur les métadonnées */}
			{capabilityOptions.length > 0 && (
				<div className="flex flex-wrap items-center gap-1.5 border-b border-line-1 px-4 py-2">
					<span className="text-xs text-foreground-tertiary">Capacités :</span>
					{capabilityOptions.map((capability) => {
						const active = filters.capabilities.includes(capability);
						return (
							<button
								key={capability}
								type="button"
								onClick={() => toggleCapabilityFilter(capability)}
								aria-pressed={active}
								className={cn("rounded-full", active ? "" : "opacity-70")}
							>
								<Badge variant={active ? capabilityVariant(capability) : "dim"} size="sm">
									{capabilityLabel(capability)}
								</Badge>
							</button>
						);
					})}
					{filters.capabilities.length > 0 && (
						<button
							type="button"
							className="text-xs text-accent underline"
							onClick={() => setFilter("capabilities", [])}
						>
							Réinitialiser
						</button>
					)}
				</div>
			)}


			{/* Détail du modèle sélectionné — métadonnées Core uniquement */}
			{selectedModel && (
				<ModelConfigPanel
					model={selectedModel}
					provider={providerOf(selectedModel)}
					isDefault={isProviderDefault(selectedModel)}
					onSetDefault={() => handleSetDefault(selectedModel)}
					onEditPreset={() =>
						setPresetTarget({ model: selectedModel, basedOn: null })
					}
					onToggleCustom={() => handleToggleCustom(selectedModel)}
					onClear={() => setSelectedModel(null)}
				/>
			)}

			<div className="min-h-0 flex-1 overflow-y-auto">
				{isLoading && models.length === 0 && (
					<div className="flex flex-col items-center justify-center py-16 text-center">
						<LoaderCircle className="mb-4 h-8 w-8 animate-spin text-accent" />
						<p className="text-sm text-foreground-tertiary">
							Chargement du catalogue Core…
						</p>
					</div>
				)}

				{!isLoading && error && (
					<div className="flex flex-col items-center justify-center py-16 text-center">
						<AlertCircle className="mb-4 h-8 w-8 text-red" />
						<p className="text-sm text-red">Erreur : {error}</p>
						<Button
							size="sm"
							variant="outline"
							className="mt-3"
							onClick={() => refetchModels()}
						>
							Réessayer
						</Button>
					</div>
				)}

				{!isLoading && !error && displayedModels.length === 0 && (
					<div className="flex flex-col items-center justify-center py-16 text-center">
						<div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10">
							<Database className="h-6 w-6 text-accent" />
						</div>
						<h2 className="text-lg font-semibold text-foreground">
							{models.length === 0
								? "Aucun modèle dans le catalogue"
								: "Aucun modèle trouvé"}
						</h2>
						<p className="mt-2 max-w-md text-sm text-foreground-tertiary">
							{models.length === 0
								? "Configurez un provider (Ollama, OpenAI…) puis testez sa connexion : le Core découvrira ses modèles."
								: "Aucun modèle ne correspond à vos filtres. Réinitialisez la recherche ou les capacités."}
						</p>
						{models.length === 0 ? (
							<a href="/providers" className="mt-3 text-sm text-accent underline">
								Ouvrir la page Providers
							</a>
						) : (
							<Button
								size="sm"
								variant="outline"
								className="mt-3"
								onClick={() => setFilters(DEFAULT_MODEL_FILTERS)}
							>
								Réinitialiser les filtres
							</Button>
						)}
					</div>
				)}

				{!isLoading && !error && displayedModels.length > 0 && (
					<>
						{view === "cards" && (
							<div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
								{displayedModels.map((model) => (
									<ModelCard
										key={modelKey(model)}
										model={model}
										pinned={isPinned(model.provider, model.id)}
										selected={
											selectedModel !== null &&
											modelKey(selectedModel) === modelKey(model)
										}
										compareSelected={compareSelection.includes(modelKey(model))}
										isProviderDefault={isProviderDefault(model)}
										onClick={() => setSelectedModel(model)}
										onPin={() => handlePin(model)}
										onCompare={() => toggleCompareSelection(model)}
									/>
								))}
							</div>
						)}

						{view === "list" && (
							<div className="divide-y divide-line-1">
								{displayedModels.map((model) => (
									<ModelListRow
										key={modelKey(model)}
										model={model}
										pinned={isPinned(model.provider, model.id)}
										compareSelected={compareSelection.includes(modelKey(model))}
										isProviderDefault={isProviderDefault(model)}
										onClick={() => setSelectedModel(model)}
										onPin={() => handlePin(model)}
										onCompare={() => toggleCompareSelection(model)}
									/>
								))}
							</div>
						)}

						{view === "table" && (
							<ModelTable
								models={displayedModels}
								sortKey={sortKey}
								sortDirection={sortDirection}
								onToggleSort={toggleSort}
								compareSelection={compareSelection}
								isPinned={isPinned}
								isProviderDefault={isProviderDefault}
								onSelect={(model) => setSelectedModel(model)}
								onPin={handlePin}
								onCompare={toggleCompareSelection}
							/>
						)}
					</>
				)}
			</div>


			{/* Dialog preset custom — création / édition (Core ModelStore) */}
			<ModelPresetDialog
				open={presetTarget !== null}
				model={presetTarget?.model ?? null}
				basedOn={presetTarget?.basedOn ?? null}
				onClose={() => setPresetTarget(null)}
				onSubmit={handlePresetSubmit}
			/>

			{/* Comparaison — uniquement les métadonnées réellement présentes */}
			<Dialog
				open={compareOpen}
				onClose={() => setCompareOpen(false)}
				title={`Comparer ${comparedModels.length} modèles`}
				size="lg"
			>
				{comparedModels.length < 2 ? (
					<p className="text-sm text-foreground-tertiary">
						Sélectionnez au moins deux modèles pour comparer leurs métadonnées.
					</p>
				) : (
					<div className="overflow-x-auto">
						<table className="w-full text-sm">
							<thead>
								<tr className="border-b border-line-1 text-left">
									<th className="px-2 py-2 text-xs uppercase text-foreground-tertiary">
										Métadonnée (Core)
									</th>
									{comparedModels.map((model) => (
										<th key={modelKey(model)} className="px-2 py-2 text-foreground">
											{model.name}
											<span className="block font-mono text-[10px] text-foreground-tertiary">
												{model.provider}
											</span>
										</th>
									))}
								</tr>
							</thead>
							<tbody>
								{buildModelComparison(comparedModels).map((row) => (
									<tr key={row.key} className="border-b border-line-1/50">
										<td className="px-2 py-2 text-foreground-tertiary">{row.label}</td>
										{row.values.map((value, index) => (
											<td
												key={`${row.key}-${index}`}
												className="px-2 py-2 text-foreground"
											>
												{comparisonValue(value)}
											</td>
										))}
									</tr>
								))}
							</tbody>
						</table>
						<p className="mt-3 text-xs text-foreground-tertiary">
							Seules les métadonnées réellement fournies par ETHAN Core sont affichées ;
							une valeur absente apparaît « — ».
						</p>
					</div>
				)}
				<div className="mt-4 flex justify-end gap-2 border-t border-line-1 pt-3">
					<Button size="sm" variant="secondary" onClick={() => setCompareSelection([])}>
						Vider la sélection
					</Button>
					<Button size="sm" onClick={() => setCompareOpen(false)}>
						Fermer
					</Button>
				</div>
			</Dialog>
		</div>
	);
}

// ── Sous-composants de présentation ─────────────────────────────────────────

interface ModelActionProps {
	model: ModelInfo;
	pinned: boolean;
	compareSelected: boolean;
	isProviderDefault: boolean;
	onClick: () => void;
	onPin: () => void;
	onCompare: () => void;
}

function CapabilityBadges({ capabilities }: { capabilities?: string[] }) {
	if (!capabilities || capabilities.length === 0) return null;
	return (
		<div className="flex flex-wrap gap-1">
			{capabilities.slice(0, 4).map((capability) => (
				<Badge
					key={capability}
					variant={capabilityVariant(capability)}
					size="sm"
				>
					{capabilityLabel(capability)}
				</Badge>
			))}
			{capabilities.length > 4 && (
				<Badge variant="dim" size="sm">
					+{capabilities.length - 4}
				</Badge>
			)}
		</div>
	);
}

function CompareToggle({
	selected,
	onToggle,
	modelName,
}: {
	selected: boolean;
	onToggle: () => void;
	modelName: string;
}) {
	return (
		<button
			type="button"
			title={selected ? "Retirer de la comparaison" : `Comparer ${modelName}`}
			aria-label={
				selected ? `Retirer ${modelName} de la comparaison` : `Comparer ${modelName}`
			}
			aria-pressed={selected}
			className={cn(
				"rounded border p-0.5 transition-colors",
				selected
					? "border-accent bg-accent text-white"
					: "border-line-1 text-foreground-tertiary hover:border-accent",
			)}
			onClick={(event) => {
				event.stopPropagation();
				onToggle();
			}}
		>
			{selected ? <Check className="h-3 w-3" /> : <GitCompare className="h-3 w-3" />}
		</button>
	);
}

function ModelCard({
	model,
	pinned,
	selected,
	compareSelected,
	isProviderDefault,
	onClick,
	onPin,
	onCompare,
}: ModelActionProps & { selected: boolean }) {
	return (
		<div
			role="button"
			tabIndex={0}
			onClick={onClick}
			onKeyDown={(event) => {
				if (event.key === "Enter" || event.key === " ") {
					event.preventDefault();
					onClick();
				}
			}}
			className={cn(
				"group relative flex cursor-pointer flex-col rounded-xl border bg-bg-1 p-4 transition-all",
				selected
					? "border-accent/60 shadow-md ring-2 ring-accent/30"
					: "border-line-1 hover:border-accent/50 hover:shadow-sm",
			)}
		>
			<div className="flex items-start justify-between gap-2">
				<div className="min-w-0">
					<p className="truncate text-sm font-medium text-foreground">{model.name}</p>
					<p className="truncate font-mono text-xs text-foreground-tertiary">
						{model.model}
					</p>
				</div>
				<div className="flex items-center gap-1">
					<CompareToggle
						selected={compareSelected}
						onToggle={onCompare}
						modelName={model.name}
					/>
					<button
						type="button"
						title={pinned ? "Désépingler" : "Épingler"}
						aria-label={pinned ? `Désépingler ${model.name}` : `Épingler ${model.name}`}
						className={cn(
							"rounded p-0.5 transition-opacity hover:bg-bg-2",
							pinned ? "opacity-100" : "opacity-0 group-hover:opacity-100",
						)}
						onClick={(event) => {
							event.stopPropagation();
							onPin();
						}}
					>
						<Star className={cn("h-4 w-4", pinned && "fill-accent text-accent")} />
					</button>
				</div>
			</div>

			<div className="mt-2 flex items-center gap-2 text-xs text-foreground-tertiary">
				<span className="truncate">{model.provider}</span>
				{model.is_custom && (
					<Badge variant="accent" size="sm">
						custom
					</Badge>
				)}
				{isProviderDefault && (
					<Badge variant="solid" size="sm">
						Défaut
					</Badge>
				)}
			</div>

			<div className="mt-3 flex flex-col gap-2">
				<p className="text-[11px] text-foreground-tertiary">
					Contexte : {model.context_length ? model.context_length.toLocaleString() : "—"}
				</p>
				<CapabilityBadges capabilities={model.capabilities} />
			</div>

			<div className="mt-3 flex items-center justify-between text-[11px] text-foreground-tertiary">
				<span>Qualité : {Math.round((model.quality_score || 0) * 100)}%</span>
				{model.is_available ? (
					<Badge variant="success" size="sm">
						{modelAvailabilityLabel(model)}
					</Badge>
				) : (
					<Badge variant="error" size="sm">
						{modelAvailabilityLabel(model)}
					</Badge>
				)}
			</div>
		</div>
	);
}

function ModelListRow({
	model,
	pinned,
	compareSelected,
	isProviderDefault,
	onClick,
	onPin,
	onCompare,
}: ModelActionProps) {
	return (
		<div
			role="button"
			tabIndex={0}
			onClick={onClick}
			onKeyDown={(event) => {
				if (event.key === "Enter" || event.key === " ") {
					event.preventDefault();
					onClick();
				}
			}}
			className="flex cursor-pointer items-center gap-3 px-4 py-2.5 hover:bg-bg-2"
		>
			<CompareToggle
				selected={compareSelected}
				onToggle={onCompare}
				modelName={model.name}
			/>
			<div className="min-w-0 flex-1">
				<div className="flex items-center gap-2">
					<span className="truncate text-sm font-medium text-foreground">{model.name}</span>
					{model.is_custom && (
						<Badge variant="accent" size="sm">
							custom
						</Badge>
					)}
					{isProviderDefault && (
						<Badge variant="solid" size="sm">
							Défaut
						</Badge>
					)}
					{!model.is_available && (
						<Badge variant="error" size="sm">
							Indisponible
						</Badge>
					)}
				</div>
				<p className="truncate font-mono text-xs text-foreground-tertiary">
					{model.provider} · {model.model}
					{model.context_length ? ` · ${model.context_length.toLocaleString()} ctx` : ""}
				</p>
			</div>
			<CapabilityBadges capabilities={model.capabilities} />
			<button
				type="button"
				title={pinned ? "Désépingler" : "Épingler"}
				aria-label={pinned ? `Désépingler ${model.name}` : `Épingler ${model.name}`}
				className="rounded p-1 hover:bg-bg-1"
				onClick={(event) => {
					event.stopPropagation();
					onPin();
				}}
			>
				<Star className={cn("h-4 w-4", pinned && "fill-accent text-accent")} />
			</button>
		</div>
	);
}


function SortableHeader({
	label,
	sortKey,
	activeKey,
	direction,
	onToggle,
}: {
	label: string;
	sortKey: ModelSortKey;
	activeKey: ModelSortKey;
	direction: SortDirection;
	onToggle: (key: ModelSortKey) => void;
}) {
	const active = sortKey === activeKey;
	return (
		<th className="px-2 py-2 text-left">
			<button
				type="button"
				onClick={() => onToggle(sortKey)}
				className={cn(
					"inline-flex items-center gap-1 text-xs uppercase",
					active ? "text-accent" : "text-foreground-tertiary hover:text-foreground",
				)}
			>
				{label}
				{active &&
					(direction === "asc" ? (
						<ArrowUp className="h-3 w-3" />
					) : (
						<ArrowDown className="h-3 w-3" />
					))}
			</button>
		</th>
	);
}

function ModelTable({
	models,
	sortKey,
	sortDirection,
	onToggleSort,
	compareSelection,
	isPinned,
	isProviderDefault,
	onSelect,
	onPin,
	onCompare,
}: {
	models: ModelInfo[];
	sortKey: ModelSortKey;
	sortDirection: SortDirection;
	onToggleSort: (key: ModelSortKey) => void;
	compareSelection: string[];
	isPinned: (providerId: string, modelId: string) => boolean;
	isProviderDefault: (model: ModelInfo) => boolean;
	onSelect: (model: ModelInfo) => void;
	onPin: (model: ModelInfo) => void;
	onCompare: (model: ModelInfo) => void;
}) {
	return (
		<table className="w-full text-sm">
			<thead className="sticky top-0 border-b border-line-1 bg-bg-1">
				<tr>
					<th className="w-8 px-2 py-2" aria-label="Comparer" />
					<SortableHeader
						label="Modèle"
						sortKey="name"
						activeKey={sortKey}
						direction={sortDirection}
						onToggle={onToggleSort}
					/>
					<SortableHeader
						label="Provider"
						sortKey="provider"
						activeKey={sortKey}
						direction={sortDirection}
						onToggle={onToggleSort}
					/>
					<SortableHeader
						label="Contexte"
						sortKey="context_length"
						activeKey={sortKey}
						direction={sortDirection}
						onToggle={onToggleSort}
					/>
					<th className="px-2 py-2 text-left text-xs uppercase text-foreground-tertiary">
						Capacités
					</th>
					<SortableHeader
						label="Qualité"
						sortKey="quality_score"
						activeKey={sortKey}
						direction={sortDirection}
						onToggle={onToggleSort}
					/>
					<SortableHeader
						label="État"
						sortKey="availability"
						activeKey={sortKey}
						direction={sortDirection}
						onToggle={onToggleSort}
					/>
					<th className="w-10 px-2 py-2" aria-label="Épingler" />
				</tr>
			</thead>
			<tbody>
				{models.map((model) => (
					<tr
						key={modelKey(model)}
						className="cursor-pointer border-b border-line-1/50 hover:bg-bg-2"
						onClick={() => onSelect(model)}
					>
						<td className="px-2 py-2">
							<CompareToggle
								selected={compareSelection.includes(modelKey(model))}
								onToggle={() => onCompare(model)}
								modelName={model.name}
							/>
						</td>
						<td className="px-2 py-2">
							<div className="flex items-center gap-2">
								<span className="text-foreground">{model.name}</span>
								{model.is_custom && (
									<Badge variant="accent" size="sm">
										custom
									</Badge>
								)}
								{isProviderDefault(model) && (
									<Badge variant="solid" size="sm">
										Défaut
									</Badge>
								)}
							</div>
							<span className="font-mono text-[10px] text-foreground-tertiary">
								{model.model}
							</span>
						</td>
						<td className="px-2 py-2 text-foreground-secondary">{model.provider}</td>
						<td className="px-2 py-2 text-foreground-secondary">
							{model.context_length ? model.context_length.toLocaleString() : "—"}
						</td>
						<td className="px-2 py-2">
							<CapabilityBadges capabilities={model.capabilities} />
						</td>


						<td className="px-2 py-2 text-foreground-secondary">
							{Math.round((model.quality_score || 0) * 100)}%
						</td>
						<td className="px-2 py-2">
							<Badge
								variant={model.is_available ? "success" : "error"}
								size="sm"
							>
								{modelAvailabilityLabel(model)}
							</Badge>
						</td>
						<td className="px-2 py-2">
							<button
								type="button"
								title={isPinned(model.provider, model.id) ? "Désépingler" : "Épingler"}
								aria-label={
									isPinned(model.provider, model.id)
										? `Désépingler ${model.name}`
										: `Épingler ${model.name}`
								}
								className="rounded p-1 hover:bg-bg-1"
								onClick={(event) => {
									event.stopPropagation();
									onPin(model);
								}}
							>
								<Star
									className={cn(
										"h-4 w-4",
										isPinned(model.provider, model.id) && "fill-accent text-accent",
									)}
								/>
							</button>
						</td>
					</tr>
				))}
			</tbody>
		</table>
	);
}




function ModelConfigPanel({
	model,
	provider,
	isDefault,
	onSetDefault,
	onEditPreset,
	onToggleCustom,
	onClear,
}: {
	model: ModelInfo;
	provider: Provider | null;
	isDefault: boolean;
	onSetDefault: () => void;
	onEditPreset: () => void;
	onToggleCustom: () => void;
	onClear: () => void;
}) {
	const editable = isModelActivationEditable(model);
	return (
		<div className="mx-4 mt-3 rounded-xl border border-line-1 bg-bg-1 p-4">
			<div className="flex flex-wrap items-start justify-between gap-3">
				<div className="min-w-0">
					<p className="text-sm font-medium text-foreground">{model.name}</p>
					<p className="truncate font-mono text-xs text-foreground-tertiary">
						{model.model} · {model.provider}
						{model.is_local ? " · local" : ""}
					</p>
				</div>
				<div className="flex flex-wrap items-center gap-2">
					{editable ? (
						<>
							<Button size="sm" variant="secondary" onClick={onToggleCustom}>
								{model.is_available ? "Désactiver la fiche" : "Activer la fiche"}
							</Button>
							<Button size="sm" variant="outline" onClick={onEditPreset}>
								<Settings2 className="h-4 w-4" /> Configurer
							</Button>
						</>
					) : (
						<>
							<Button size="sm" variant="outline" onClick={onEditPreset}>
								<Plus className="h-4 w-4" /> Créer un preset
							</Button>
							{provider &&
								(isDefault ? (
									<Badge variant="accent" size="sm">
										Modèle par défaut du provider
									</Badge>
								) : (
									<Button size="sm" variant="secondary" onClick={onSetDefault}>
										Définir comme modèle par défaut
									</Button>
								))}
						</>
					)}
					<Button size="sm" variant="ghost" onClick={onClear} title="Fermer">
						<X className="h-4 w-4" />
					</Button>
				</div>
			</div>

			<div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs sm:grid-cols-4">
				<div>
					<p className="text-foreground-tertiary">Source</p>
					<p className="text-foreground">{model.is_custom ? "custom" : "discovered"}</p>
				</div>
				<div>
					<p className="text-foreground-tertiary">Contexte</p>
					<p className="text-foreground">
						{model.context_length ? model.context_length.toLocaleString() : "—"}
					</p>
				</div>
				<div>
					<p className="text-foreground-tertiary">Qualité (Core)</p>
					<p className="text-foreground">{Math.round((model.quality_score || 0) * 100)}%</p>
				</div>
				<div>
					<p className="text-foreground-tertiary">Disponibilité</p>
					<p className="text-foreground">{modelAvailabilityLabel(model)}</p>
				</div>
			</div>

			{model.capabilities && model.capabilities.length > 0 && (
				<div className="mt-3">
					<CapabilityBadges capabilities={model.capabilities} />
				</div>
			)}

			<p className="mt-3 text-[11px] text-foreground-tertiary">
				{editable
					? "Fiche custom : activation et paramètres avancés gérés par ETHAN Core (ModelStore)."
					: "Modèle découvert : son état dépend du provider. Le « modèle par défaut » est le default_model du provider dans ETHAN Core ; un preset permet d'enregistrer des paramètres de génération."}
			</p>
		</div>
	);
}
