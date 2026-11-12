/**
 * ETHAN WebUI — Logique de présentation du catalogue de modèles.
 *
 * Fonctions PURES (aucun appel réseau, aucune règle métier) consommées par
 * le workspace Models : filtres, tri et comparaison basée uniquement sur les
 * métadonnées réellement renvoyées par le Core (GET /models). Une donnée
 * absente n'est jamais inventée : elle est simplement omise de la
 * comparaison.
 */

import type { ModelInfo } from "@/lib/api/models";

export type ModelSourceFilter = "all" | "discovered" | "custom";
export type ModelAvailabilityFilter = "all" | "available" | "unavailable";
export type ModelSortKey =
	| "name"
	| "provider"
	| "context_length"
	| "quality_score"
	| "availability";
export type SortDirection = "asc" | "desc";

export interface ModelCatalogFilters {
	query: string;
	/** Provider id (`null` = tous). */
	providerId: string | null;
	/** Capacités requises (ET logique) — valeurs réelles du Core. */
	capabilities: string[];
	source: ModelSourceFilter;
	availability: ModelAvailabilityFilter;
	/** Limiter aux modèles épinglés (préférence UI locale). */
	pinnedOnly?: boolean;
}

export const DEFAULT_MODEL_FILTERS: ModelCatalogFilters = {
	query: "",
	providerId: null,
	capabilities: [],
	source: "all",
	availability: "all",
	pinnedOnly: false,
};

/** Filtre le catalogue (recherche texte, provider, capacités, source, dispo). */
export function filterModelCatalog(
	models: ModelInfo[],
	filters: ModelCatalogFilters,
	isPinned?: (model: ModelInfo) => boolean,
): ModelInfo[] {
	const query = filters.query.trim().toLowerCase();

	return models.filter((model) => {
		if (filters.providerId && model.provider !== filters.providerId) return false;

		if (filters.source === "custom" && !model.is_custom) return false;
		if (filters.source === "discovered" && model.is_custom) return false;

		if (filters.availability === "available" && !model.is_available) return false;
		if (filters.availability === "unavailable" && model.is_available) return false;

		if (filters.capabilities.length > 0) {
			const caps = model.capabilities ?? [];
			if (!filters.capabilities.every((capability) => caps.includes(capability))) {
				return false;
			}
		}

		if (filters.pinnedOnly && isPinned && !isPinned(model)) return false;

		if (query) {
			const haystack = [
				model.name,
				model.model,
				model.id,
				model.provider,
				...(model.capabilities ?? []),
			]
				.join(" ")
				.toLowerCase();
			if (!haystack.includes(query)) return false;
		}

		return true;
	});
}

/** Tri stable du catalogue selon une colonne réelle. */
export function sortModelCatalog(
	models: ModelInfo[],
	key: ModelSortKey,
	direction: SortDirection = "asc",
): ModelInfo[] {
	const factor = direction === "asc" ? 1 : -1;
	return [...models].sort((a, b) => {
		switch (key) {
			case "context_length":
				return factor * ((a.context_length || 0) - (b.context_length || 0));
			case "quality_score":
				return factor * ((a.quality_score || 0) - (b.quality_score || 0));
			case "availability":
				return factor * (Number(a.is_available) - Number(b.is_available));
			case "provider":
				return (
					factor * a.provider.localeCompare(b.provider) ||
					a.name.localeCompare(b.name)
				);
			default:
				return factor * a.name.localeCompare(b.name);
		}
	});
}

export interface ComparisonRow {
	key: string;
	label: string;
	/** Une valeur par modèle comparé (même ordre) ; null = métadonnée absente. */
	values: (string | number | null)[];
}

const EMPTY_VALUE = "—";

/**
 * Libellé de joignabilité réel d'un modèle découvert (vue Liste/Table).
 *
 * N'est appliqué qu'aux modèles DÉCOUVERTS : une fiche custom n'a pas de
 * joignabilité testable par le Core (voir `modelStateLabel`).
 */
export function modelAvailabilityLabel(model: ModelInfo): string {
	return model.is_available ? "Disponible" : "Indisponible";
}

/**
 * Construit la comparaison de 2+ modèles.
 *
 * Une ligne n'apparaît que si AU MOINS un modèle possède réellement la
 * métadonnée (valeur non nulle / non vide). Les lignes absentes partout sont
 * omises — la comparaison ne montre jamais de champ inventé.
 */
export function buildModelComparison(models: ModelInfo[]): ComparisonRow[] {
	if (models.length === 0) return [];

	const candidates: ComparisonRow[] = [
		{
			key: "provider",
			label: "Provider",
			values: models.map((m) => m.provider || null),
		},
		{
			key: "source",
			label: "Source",
			values: models.map((m) => (m.is_custom ? "custom" : "discovered")),
		},
		{
			key: "context_length",
			label: "Contexte",
			values: models.map((m) =>
				m.context_length ? m.context_length.toLocaleString() : null,
			),
		},
		{
			key: "capabilities",
			label: "Capacités",
			values: models.map((m) =>
				m.capabilities && m.capabilities.length > 0
					? m.capabilities.join(", ")
					: null,
			),
		},
		{
			// La ligne reflète l'état CONNU du Core : joignabilité pour un
			// modèle découvert, activation pour une fiche custom (le Core ne
			// peut pas tester la joignabilité d'une fiche).
			key: "availability",
			label: "État (Core)",
			values: models.map((m) => modelStateLabel(m)),
		},
		{
			key: "provider_declared",
			label: "Provider déclaré",
			values: models.map((m) => (hasKnownProvider(m) ? m.provider : null)),
		},
		{
			key: "quality_score",
			label: "Qualité (Core)",
			values: models.map((m) =>
				m.quality_score ? `${Math.round(m.quality_score * 100)}%` : null,
			),
		},
		{
			// Métadonnées réellement déclarées par les adapters Core — la
			// ligne est filtrée (voir plus bas) si aucun modèle ne les porte.
			key: "pricing",
			label: "Tarifs déclarés (Core)",
			values: models.map((m) =>
				m.pricing && Object.keys(m.pricing).length > 0
					? Object.entries(m.pricing)
							.map(([k, v]) => `${k}=${String(v)}`)
							.join(", ")
					: null,
			),
		},
		{
			key: "avg_latency_ms",
			label: "Latence déclarée (Core)",
			values: models.map((m) =>
				typeof m.avg_latency_ms === "number" && m.avg_latency_ms > 0
					? `${Math.round(m.avg_latency_ms)} ms`
					: null,
			),
		},
		{
			key: "is_local",
			label: "Local",
			values: models.map((m) => (m.is_local ? "Oui" : null)),
		},
		{
			key: "is_private",
			label: "Privé",
			values: models.map((m) => (m.is_private ? "Oui" : null)),
		},
		{
			key: "params",
			label: "Paramètres (fiche custom)",
			values: models.map((m) => {
				const entries = Object.entries(m.params ?? {});
				return entries.length > 0
					? entries.map(([key, value]) => `${key}=${String(value)}`).join(", ")
					: null;
			}),
		},
	];

	return candidates.filter((row) => row.values.some((value) => value !== null));
}

/** Valeur affichable pour une cellule de comparaison (— si absente). */
export function comparisonValue(value: string | number | null): string {
	return value === null || value === "" ? EMPTY_VALUE : String(value);
}

/**
 * Libellé du provider d'un modèle.
 *
 * `provider` est l'identifiant du SERVICE (jamais un identifiant de modèle).
 * Une fiche custom dont le Core ne connaît pas de provider renvoie "" : on
 * affiche alors un libellé explicite plutôt que d'inventer un service ou
 * d'afficher un nom de modèle dans la colonne « Provider ».
 */
export function modelProviderLabel(model: ModelInfo): string {
	return model.provider || "Provider non déclaré";
}

/** true si le Core connaît un provider (service) pour ce modèle. */
export function hasKnownProvider(model: ModelInfo): boolean {
	return Boolean(model.provider);
}

/**
 * Libellé d'état d'un modèle.
 *
 * - Modèle découvert : le Core connaît la joignabilité → Disponible /
 *   Indisponible.
 * - Fiche custom : le Core ne peut PAS tester la joignabilité ; seul
 *   l'activation administrative est connue. On affiche donc Actif / Inactif
 *   plutôt qu'un « Disponible » qui usurperait une information inexistante.
 */
export function modelStateLabel(model: ModelInfo): string {
	if (model.is_custom) {
		return model.is_active === false ? "Inactif" : "Actif";
	}
	return modelAvailabilityLabel(model);
}

/** Un modèle découvert est géré par son provider (pas d'activation locale). */
export function isModelActivationEditable(model: ModelInfo): boolean {
	return model.is_custom;
}

