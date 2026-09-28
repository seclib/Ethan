/**
 * Tests WebUI — logique de présentation du catalogue de modèles.
 *
 * Fonctions PURES (aucun appel réseau) : filtres, tri, comparaison. Invariants
 * couverts : aucune métadonnée inventée (ligne omise si absente partout,
 * « — » si absente pour un modèle), valeurs triées/ordonnées de façon stable.
 */

import {
	buildModelComparison,
	comparisonValue,
	DEFAULT_MODEL_FILTERS,
	filterModelCatalog,
	hasKnownProvider,
	isModelActivationEditable,
	modelAvailabilityLabel,
	modelProviderLabel,
	modelStateLabel,
	sortModelCatalog,
} from "@/lib/llm/model-catalog";
import type { ModelInfo } from "@/lib/api/models";

function makeModel(over: Partial<ModelInfo> = {}): ModelInfo {
	return {
		id: "m-llama",
		name: "Llama 3.2",
		model: "llama3.2",
		provider: "ollama",
		context_length: 131072,
		is_local: true,
		is_private: true,
		quality_score: 0.8,
		capabilities: ["chat", "code"],
		is_available: true,
		is_custom: false,
		source: "discovered",
		...over,
	};
}

describe("filterModelCatalog", () => {
	const models = [
		makeModel(),
		makeModel({
			id: "m-phi",
			name: "Phi Mini",
			model: "phi-mini",
			capabilities: ["vision"],
			is_available: false,
		}),
		makeModel({
			id: "c-1",
			name: "Mon preset",
			model: "llama3.2-custom",
			is_custom: true,
			source: "custom",
			provider: "openai",
			capabilities: [],
		}),
	];

	it("recherche : nom, modèle technique, provider et capacités", () => {
		expect(
			filterModelCatalog(models, { ...DEFAULT_MODEL_FILTERS, query: "phi" }),
		).toHaveLength(1);
		expect(
			filterModelCatalog(models, { ...DEFAULT_MODEL_FILTERS, query: "openai" }),
		).toHaveLength(1);
		expect(
			filterModelCatalog(models, { ...DEFAULT_MODEL_FILTERS, query: "vision" }),
		).toHaveLength(1);
		expect(
			filterModelCatalog(models, { ...DEFAULT_MODEL_FILTERS, query: "zzz" }),
		).toHaveLength(0);
	});

	it("filtres provider, source et disponibilité", () => {
		expect(
			filterModelCatalog(models, { ...DEFAULT_MODEL_FILTERS, providerId: "openai" }),
		).toHaveLength(1);
		expect(
			filterModelCatalog(models, { ...DEFAULT_MODEL_FILTERS, source: "custom" }),
		).toHaveLength(1);
		expect(
			filterModelCatalog(models, { ...DEFAULT_MODEL_FILTERS, source: "discovered" }),
		).toHaveLength(2);
		expect(
			filterModelCatalog(models, {
				...DEFAULT_MODEL_FILTERS,
				availability: "unavailable",
			}),
		).toHaveLength(1);
	});

	it("capacités requises en ET logique", () => {
		expect(
			filterModelCatalog(models, {
				...DEFAULT_MODEL_FILTERS,
				capabilities: ["chat", "code"],
			}),
		).toHaveLength(1);
		expect(
			filterModelCatalog(models, {
				...DEFAULT_MODEL_FILTERS,
				capabilities: ["chat", "vision"],
			}),
		).toHaveLength(0);
	});

	it("pinnedOnly s'appuie sur le callback fourni", () => {
		const isPinned = (model: ModelInfo) => model.id === "m-phi";
		expect(
			filterModelCatalog(
				models,
				{ ...DEFAULT_MODEL_FILTERS, pinnedOnly: true },
				isPinned,
			),
		).toHaveLength(1);
	});
});

describe("sortModelCatalog", () => {
	it("tri par nom (asc/desc) sans muter l'entrée", () => {
		const zeta = makeModel({ name: "Zeta" });
		const alpha = makeModel({ id: "m-alpha", name: "Alpha" });
		const input = [zeta, alpha];
		const sorted = sortModelCatalog(input, "name", "asc");
		expect(sorted.map((m) => m.name)).toEqual(["Alpha", "Zeta"]);
		expect(sortModelCatalog(input, "name", "desc").map((m) => m.name)).toEqual([
			"Zeta",
			"Alpha",
		]);
		expect(input[0]).toBe(zeta);
	});

	it("contexte/qualité : valeur absente comptée comme 0", () => {
		const models = [
			makeModel({ name: "A", context_length: 0 }),
			makeModel({ name: "B", context_length: 8192 }),
		];
		expect(
			sortModelCatalog(models, "context_length", "asc").map((m) => m.name),
		).toEqual(["A", "B"]);
		expect(
			sortModelCatalog(
				[
					makeModel({ name: "A", quality_score: 0 }),
					makeModel({ name: "B", quality_score: 0.9 }),
				],
				"quality_score",
				"desc",
			).map((m) => m.name),
		).toEqual(["B", "A"]);
	});

	it("disponibilité : tri par état réel (indisponibles d'abord en asc)", () => {
		const models = [
			makeModel({ name: "A", is_available: true }),
			makeModel({ name: "B", is_available: false }),
		];
		expect(
			sortModelCatalog(models, "availability", "asc").map((m) => m.name),
		).toEqual(["B", "A"]);
		expect(
			sortModelCatalog(models, "availability", "desc").map((m) => m.name),
		).toEqual(["A", "B"]);
	});
});

// ── Frontière Provider / Modèle ────────────────────────────────────────────
// Régression : le Core plaçait autrefois `base_model_id` (un identifiant de
// MODÈLE) dans le champ `provider`, ce qui rendait une fiche custom
// infiltrable/imprimable sous un faux nom de service.
describe("frontière Provider / Modèle", () => {
	it("le provider d'une fiche custom est un service, pas un nom de modèle", () => {
		const custom = makeModel({
			id: "c-1",
			name: "Mon preset",
			is_custom: true,
			source: "custom",
			provider: "ollama",
			model: "llama3.2-custom",
			base_model_id: "llama3.2",
		});
		// `provider` = service ; `base_model_id` = modèle de base. Distincts.
		expect(custom.provider).toBe("ollama");
		expect(custom.base_model_id).toBe("llama3.2");
		expect(hasKnownProvider(custom)).toBe(true);
		expect(modelProviderLabel(custom)).toBe("ollama");
	});

	it("une fiche custom est filtrable par son VRAI provider", () => {
		const custom = makeModel({
			id: "c-1",
			name: "Mon preset",
			is_custom: true,
			source: "custom",
			provider: "openai",
			model: "gpt-4o-mini",
			base_model_id: "gpt-4o",
		});
		const discovered = makeModel({ id: "m-1", provider: "ollama" });
		const all = [discovered, custom];

		expect(
			filterModelCatalog(all, { ...DEFAULT_MODEL_FILTERS, providerId: "openai" }),
		).toEqual([custom]);
		expect(
			filterModelCatalog(all, { ...DEFAULT_MODEL_FILTERS, providerId: "ollama" }),
		).toEqual([discovered]);
	});

	it("provider non déclaré : libellé explicite, aucun service inventé", () => {
		// Fiche créée avant l'introduction du champ `provider` côté Core.
		const orphan = makeModel({
			id: "c-legacy",
			is_custom: true,
			source: "custom",
			provider: "",
			base_model_id: "llama3.2",
		});
		expect(hasKnownProvider(orphan)).toBe(false);
		expect(modelProviderLabel(orphan)).toBe("Provider non déclaré");
		// Le nom du modèle de base ne doit surtout pas s'y substituer.
		expect(modelProviderLabel(orphan)).not.toBe("llama3.2");
	});

	it("état d'une fiche custom = activation, pas joignabilité inventée", () => {
		// Le Core ne peut pas tester la joignabilité d'une fiche : il affiche
		// l'activation administrative plutôt qu'un « Disponible » usurpé.
		const active = makeModel({ is_custom: true, is_available: true, is_active: true });
		const inactive = makeModel({ is_custom: true, is_available: false, is_active: false });
		expect(modelStateLabel(active)).toBe("Actif");
		expect(modelStateLabel(inactive)).toBe("Inactif");

		// Un modèle découvert, lui, a une joignabilité réellement mesurée.
		const down = makeModel({ is_custom: false, is_available: false, is_active: null });
		expect(modelStateLabel(down)).toBe("Indisponible");
		expect(modelStateLabel(makeModel({ is_available: true }))).toBe("Disponible");
	});

	it("la comparaison omet 'Provider déclaré' si aucun modèle n'en a", () => {
		const rows = buildModelComparison([
			makeModel({ provider: "" }),
			makeModel({ id: "m-2", provider: "" }),
		]);
		expect(rows.find((r) => r.key === "provider_declared")).toBeUndefined();
		// La ligne « provider » reste : elle porte le modèle de base, mais
		// « Provider déclaré » ne ment pas sur une absence.
		const declared = buildModelComparison([
			makeModel({ provider: "ollama" }),
			makeModel({ id: "m-2", provider: "" }),
		]).find((r) => r.key === "provider_declared");
		expect(declared?.values).toEqual(["ollama", null]);
	});
});

describe("buildModelComparison", () => {
	it("lignes ordonnées, valeurs alignées sur l'ordre des modèles", () => {
		const rows = buildModelComparison([
			makeModel({ context_length: 131072 }),
			makeModel({ id: "m-qwen", name: "Qwen", model: "qwen", context_length: 0 }),
		]);
		expect(rows.map((row) => row.key)).toEqual([
			"provider",
			"source",
			"context_length",
			"capabilities",
			"availability",
			"provider_declared",
			"quality_score",
			"is_local",
			"is_private",
		]);
		const context = rows.find((row) => row.key === "context_length");
		expect(context?.values[1]).toBeNull();
		// séparateur de milliers local (espace, insécable ou virgule)
		expect((context?.values[0] ?? "").replace(/\D/g, "")).toBe("131072");
	});

	it("ligne omise si absente pour TOUS les modèles (aucun champ inventé)", () => {
		const rows = buildModelComparison([
			makeModel({ quality_score: 0, is_private: false, context_length: 0 }),
			makeModel({ quality_score: 0, is_private: false, context_length: 0 }),
		]);
		const keys = rows.map((row) => row.key);
		expect(keys).not.toContain("quality_score");
		expect(keys).not.toContain("context_length");
		expect(keys).not.toContain("is_private");
	});

	it("ligne conservée dès qu'un modèle porte la métadonnée", () => {
		const rows = buildModelComparison([
			makeModel({ quality_score: 0 }),
			makeModel({ id: "m-2", quality_score: 0.9 }),
		]);
		const quality = rows.find((row) => row.key === "quality_score");
		expect(quality).toBeDefined();
		expect(quality?.values).toEqual([null, "90%"]);
	});

	it("params custom formatés key=value", () => {
		const rows = buildModelComparison([
			makeModel({ is_custom: true, params: { temperature: 0.2 } }),
		]);
		const params = rows.find((row) => row.key === "params");
		expect(params?.values).toEqual(["temperature=0.2"]);
	});
});

describe("valeurs affichables", () => {
	it("comparisonValue : « — » si absente", () => {
		expect(comparisonValue(null)).toBe("—");
		expect(comparisonValue("")).toBe("—");
		expect(comparisonValue(131072)).toBe("131072");
	});

	it("modelAvailabilityLabel reflète l'état réel du Core", () => {
		expect(modelAvailabilityLabel(makeModel())).toBe("Disponible");
		expect(modelAvailabilityLabel(makeModel({ is_available: false }))).toBe(
			"Indisponible",
		);
	});

	it("activation éditable uniquement pour les fiches custom", () => {
		expect(isModelActivationEditable(makeModel())).toBe(false);
		expect(
			isModelActivationEditable(makeModel({ is_custom: true, source: "custom" })),
		).toBe(true);
	});
});

