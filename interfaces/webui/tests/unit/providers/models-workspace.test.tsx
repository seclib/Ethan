/**
 * Tests WebUI — ModelsWorkspace (catalogue de modèles ETHAN Core).
 *
 * Hooks Core mockés (useModels / useProviders) et mutations mockées : ces
 * tests valident le rendu, les filtres/vues et l'orchestration des actions.
 * Aucune logique métier n'est réimplémentée ici (règle AGENTS.md) ; invariant
 * couvert : les valeurs affichées sont exactement celles fournies par le Core
 * (aucun registre parallèle, aucune capacité inventée).
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { ModelsWorkspace } from "@/components/features/providers/components/models-workspace";
import { useModels } from "@/components/features/providers/hooks/use-models";
import { useProviders } from "@/components/features/providers/hooks/use-providers";
import { toggleModel } from "@/lib/api/models";
import type { ModelInfo } from "@/lib/api/models";
import type { Provider } from "@/lib/api/providers";

jest.mock("@/components/features/providers/hooks/use-models", () => ({
	useModels: jest.fn(),
}));
jest.mock("@/components/features/providers/hooks/use-providers", () => ({
	useProviders: jest.fn(),
}));
jest.mock("@/lib/api/models", () => ({
	createModel: jest.fn(),
	updateModel: jest.fn(),
	toggleModel: jest.fn(),
}));

const refetchModels = jest.fn();
const updateProviderAsync = jest.fn();
const pinModel = jest.fn();
const unpinModel = jest.fn();
let pinned: { providerId: string; modelId: string }[] = [];

const ollama: Provider = {
	id: "ollama",
	name: "Ollama",
	type: "ollama",
	enabled: true,
	status: "connected",
	default_model: "qwen2.5-coder",
	is_default: false,
	base_url: "http://host:11434",
	models: [],
};

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

interface SetupOpts {
	providers?: Provider[];
	providersLoading?: boolean;
	providersError?: string | null;
	modelsLoading?: boolean;
	modelsError?: string | null;
	isPinned?: (providerId: string, modelId: string) => boolean;
}

function setup(models: ModelInfo[], opts: SetupOpts = {}) {
	(useModels as jest.Mock).mockReturnValue({
		providers: opts.providers ?? [ollama],
		providersLoading: opts.providersLoading ?? false,
		providersError: opts.providersError ?? null,
		models,
		modelsLoading: opts.modelsLoading ?? false,
		modelsError: opts.modelsError ?? null,
		refetchModels,
		pinned,
		pinModel,
		unpinModel,
		isPinned:
			opts.isPinned ??
			((providerId: string, modelId: string) =>
				pinned.some((p) => p.providerId === providerId && p.modelId === modelId)),
	});
	(useProviders as jest.Mock).mockReturnValue({ updateProviderAsync });
}

beforeEach(() => {
	jest.clearAllMocks();
	pinned = [];
	refetchModels.mockResolvedValue(undefined);
	updateProviderAsync.mockResolvedValue(undefined);
	(toggleModel as jest.Mock).mockResolvedValue(undefined);
});

describe("ModelsWorkspace — recherche et filtres", () => {
	it("affiche les modèles du Core (vue Cartes par défaut)", () => {
		setup([
			makeModel(),
			makeModel({ id: "m-qwen", name: "Qwen 2.5", model: "qwen2.5" }),
		]);
		render(<ModelsWorkspace />);
		expect(screen.getByRole("heading", { name: "Models" })).toBeInTheDocument();
		expect(screen.getByText("Llama 3.2")).toBeInTheDocument();
		expect(screen.getByText("Qwen 2.5")).toBeInTheDocument();
	});

	it("recherche textuelle : filtre puis réinitialise", () => {
		setup([
			makeModel(),
			makeModel({ id: "m-qwen", name: "Qwen 2.5", model: "qwen2.5" }),
		]);
		render(<ModelsWorkspace />);
		fireEvent.change(screen.getByLabelText("Rechercher un modèle"), {
			target: { value: "llama3.2" },
		});
		expect(screen.getByText("Llama 3.2")).toBeInTheDocument();
		expect(screen.queryByText("Qwen 2.5")).toBeNull();
		fireEvent.change(screen.getByLabelText("Rechercher un modèle"), {
			target: { value: "zzz" },
		});
		expect(screen.getByText("Aucun modèle trouvé")).toBeInTheDocument();
		fireEvent.click(screen.getByRole("button", { name: "Réinitialiser les filtres" }));
		expect(screen.getByText("Llama 3.2")).toBeInTheDocument();
		expect(screen.getByText("Qwen 2.5")).toBeInTheDocument();
	});

	it("filtres disponibilité / source / provider sur les valeurs réelles du Core", () => {
		const openai: Provider = {
			...ollama,
			id: "openai",
			name: "OpenAI",
			type: "openai",
			default_model: "gpt-4o",
		};
		setup(
			[
				makeModel(),
				makeModel({
					id: "m-phi",
					name: "Phi Mini",
					model: "phi-mini",
					is_available: false,
					capabilities: ["vision"],
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
			],
			{ providers: [ollama, openai] },
		);
		render(<ModelsWorkspace />);
		fireEvent.change(screen.getByLabelText("Filtrer par disponibilité"), {
			target: { value: "unavailable" },
		});
		expect(screen.getByText("Phi Mini")).toBeInTheDocument();
		expect(screen.queryByText("Llama 3.2")).toBeNull();
		fireEvent.change(screen.getByLabelText("Filtrer par disponibilité"), {
			target: { value: "all" },
		});
		fireEvent.change(screen.getByLabelText("Filtrer par source"), {
			target: { value: "custom" },
		});
		expect(screen.getByText("Mon preset")).toBeInTheDocument();
		expect(screen.queryByText("Llama 3.2")).toBeNull();
		fireEvent.change(screen.getByLabelText("Filtrer par source"), {
			target: { value: "all" },
		});
		fireEvent.change(screen.getByLabelText("Filtrer par provider"), {
			target: { value: "openai" },
		});
		expect(screen.getByText("Mon preset")).toBeInTheDocument();
		expect(screen.queryByText("Phi Mini")).toBeNull();
	});

	it("filtres de capacités : union réelle du Core, aucune capacité inventée", () => {
		setup([
			makeModel(),
			makeModel({
				id: "m-phi",
				name: "Phi Mini",
				model: "phi-mini",
				is_available: false,
				capabilities: ["vision"],
			}),
		]);
		render(<ModelsWorkspace />);
		expect(screen.getByRole("button", { name: "Chat" })).toHaveAttribute(
			"aria-pressed",
			"false",
		);
		expect(screen.getByRole("button", { name: "Code" })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: "Vision" })).toBeInTheDocument();
		expect(screen.queryByRole("button", { name: "Audio" })).toBeNull();
		fireEvent.click(screen.getByRole("button", { name: "Vision" }));
		expect(screen.getByText("Phi Mini")).toBeInTheDocument();
		expect(screen.queryByText("Llama 3.2")).toBeNull();
		expect(screen.getByRole("button", { name: "Vision" })).toHaveAttribute(
			"aria-pressed",
			"true",
		);
		fireEvent.click(screen.getByRole("button", { name: "Réinitialiser" }));
		expect(screen.getByText("Llama 3.2")).toBeInTheDocument();
	});
});

describe("ModelsWorkspace — états Core", () => {
	it("chargement du catalogue", () => {
		setup([], { modelsLoading: true });
		render(<ModelsWorkspace />);
		expect(screen.getByText("Chargement du catalogue Core…")).toBeInTheDocument();
	});

	it("erreur d'accès Core + Réessayer → refetch", () => {
		setup([], { modelsError: "connexion refusée" });
		render(<ModelsWorkspace />);
		expect(screen.getByText(/Erreur : connexion refusée/)).toBeInTheDocument();
		fireEvent.click(screen.getByRole("button", { name: "Réessayer" }));
		expect(refetchModels).toHaveBeenCalled();
	});

	it("catalogue vide → invitation vers la page Providers", () => {
		setup([]);
		render(<ModelsWorkspace />);
		expect(screen.getByText("Aucun modèle dans le catalogue")).toBeInTheDocument();
		expect(
			screen.getByRole("link", { name: "Ouvrir la page Providers" }),
		).toHaveAttribute("href", "/providers");
	});
});

describe("ModelsWorkspace — vues et tri", () => {
	const two = [
		makeModel({ id: "m-zeta", name: "Zeta", model: "zeta", context_length: 8192 }),
		makeModel({ id: "m-alpha", name: "Alpha", model: "alpha", context_length: 131072 }),
	];

	it("bascule Cartes → Liste → Table", () => {
		setup(two);
		render(<ModelsWorkspace />);
		fireEvent.click(screen.getByRole("button", { name: "Vue Liste" }));
		expect(screen.getByRole("button", { name: "Vue Liste" })).toHaveAttribute(
			"aria-pressed",
			"true",
		);
		expect(screen.getByText("Alpha")).toBeInTheDocument();
		fireEvent.click(screen.getByRole("button", { name: "Vue Table" }));
		expect(screen.getAllByRole("row").length).toBeGreaterThanOrEqual(3);
		expect(screen.getByText("Qualité")).toBeInTheDocument();
	});

	it("tri par Contexte dans la table (colonnes triables)", () => {
		setup(two);
		render(<ModelsWorkspace />);
		fireEvent.click(screen.getByRole("button", { name: "Vue Table" }));
		let rows = screen.getAllByRole("row");
		// tri alphabétique par défaut
		expect(rows[1]).toHaveTextContent("Alpha");
		expect(rows[2]).toHaveTextContent("Zeta");
		fireEvent.click(screen.getByRole("button", { name: "Contexte" }));
		rows = screen.getAllByRole("row");
		// 8 192 avant 131 072
		expect(rows[1]).toHaveTextContent("Zeta");
		expect(rows[2]).toHaveTextContent("Alpha");
	});
});

describe("ModelsWorkspace — actions Core", () => {
	it("« Définir comme modèle par défaut » → updateProviderAsync(provider, { default_model })", async () => {
		setup([makeModel()]);
		render(<ModelsWorkspace />);
		fireEvent.click(screen.getByText("Llama 3.2"));
		fireEvent.click(
			screen.getByRole("button", { name: "Définir comme modèle par défaut" }),
		);
		await waitFor(() =>
			expect(updateProviderAsync).toHaveBeenCalledWith("ollama", {
				default_model: "llama3.2",
			}),
		);
	});

	it("modèle déjà par défaut → badge, pas de bouton", () => {
		setup([makeModel({ model: "qwen2.5-coder" })]);
		render(<ModelsWorkspace />);
		fireEvent.click(screen.getByText("Llama 3.2"));
		expect(screen.getByText("Modèle par défaut du provider")).toBeInTheDocument();
		expect(
			screen.queryByRole("button", { name: "Définir comme modèle par défaut" }),
		).toBeNull();
	});

	it("fiche custom activable ; modèle découvert non éditable", async () => {
		setup([
			makeModel(),
			makeModel({
				id: "c-1",
				name: "Mon preset",
				model: "llama3.2-custom",
				is_custom: true,
				source: "custom",
			}),
		]);
		render(<ModelsWorkspace />);
		fireEvent.click(screen.getByText("Mon preset"));
		fireEvent.click(screen.getByRole("button", { name: "Désactiver la fiche" }));
		await waitFor(() => expect(toggleModel).toHaveBeenCalledWith("c-1"));
		expect(
			screen.getByText(/Fiche custom : activation et paramètres avancés gérés par ETHAN Core/),
		).toBeInTheDocument();
		fireEvent.click(screen.getByText("Llama 3.2"));
		expect(
			screen.queryByRole("button", { name: "Désactiver la fiche" }),
		).toBeNull();
		expect(
			screen.getByRole("button", { name: /Créer un preset/ }),
		).toBeInTheDocument();
		expect(
			screen.getByText(/Modèle découvert : son état dépend du provider/),
		).toBeInTheDocument();
	});

	it("épinglage délégué au hook UI (pin puis unpin)", () => {
		setup([makeModel()]);
		render(<ModelsWorkspace />);
		fireEvent.click(screen.getByRole("button", { name: "Épingler Llama 3.2" }));
		expect(pinModel).toHaveBeenCalledWith("ollama", "m-llama");
	});

	it("modèle épinglé → Désépingler", () => {
		setup([makeModel()], { isPinned: () => true });
		render(<ModelsWorkspace />);
		fireEvent.click(screen.getByRole("button", { name: "Désépingler Llama 3.2" }));
		expect(unpinModel).toHaveBeenCalledWith("ollama", "m-llama");
	});
});

describe("ModelsWorkspace — comparaison", () => {
	it("2 modèles → métadonnées réelles, lignes absentes omises", async () => {
		setup([
			makeModel({ quality_score: 0, is_private: false }),
			makeModel({
				id: "m-qwen",
				name: "Qwen 2.5",
				model: "qwen2.5",
				quality_score: 0,
				is_private: false,
				is_local: false,
				context_length: 0,
			}),
		]);
		render(<ModelsWorkspace />);
		expect(screen.getByRole("button", { name: "Comparer (0)" })).toBeDisabled();
		fireEvent.click(screen.getByRole("button", { name: "Comparer Llama 3.2" }));
		fireEvent.click(screen.getByRole("button", { name: "Comparer Qwen 2.5" }));
		fireEvent.click(screen.getByRole("button", { name: "Comparer (2)" }));
		await screen.findByText("Comparer 2 modèles");
		expect(
			screen.getByText(/Seules les métadonnées réellement fournies/),
		).toBeInTheDocument();
		expect(screen.getByText("Disponibilité")).toBeInTheDocument();
		// qualité absente pour TOUS → ligne omise (aucune valeur inventée)
		expect(screen.queryByText("Qualité (Core)")).toBeNull();
		expect(screen.queryByText("Privé")).toBeNull();
		// qualité/ctx absents pour Qwen → « — » dans sa colonne
		expect(screen.getAllByText(/131\D072/).length).toBeGreaterThan(0);
		expect(screen.getAllByText("—").length).toBeGreaterThan(0);
	});

	it("comparaison limitée à 3 modèles", () => {
		setup([
			makeModel(),
			makeModel({ id: "m-qwen", name: "Qwen 2.5", model: "qwen2.5" }),
			makeModel({ id: "m-phi", name: "Phi Mini", model: "phi-mini" }),
			makeModel({
				id: "c-1",
				name: "Mon preset",
				model: "llama3.2-custom",
				is_custom: true,
				source: "custom",
			}),
		]);
		render(<ModelsWorkspace />);
		fireEvent.click(screen.getByRole("button", { name: "Comparer Llama 3.2" }));
		fireEvent.click(screen.getByRole("button", { name: "Comparer Qwen 2.5" }));
		fireEvent.click(screen.getByRole("button", { name: "Comparer Phi Mini" }));
		fireEvent.click(screen.getByRole("button", { name: "Comparer Mon preset" }));
		expect(screen.getByRole("button", { name: "Comparer (3)" })).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: "Comparer Mon preset" }),
		).toHaveAttribute("aria-pressed", "false");
	});
});


