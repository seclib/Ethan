/**
 * Tests WebUI — ProvidersWorkspace (workspace de gestion des providers LLM).
 *
 * Invariants couverts (règle AGENTS.md — l'interface révèle, elle ne
 * redéfinit pas ; ADR-3002 providers source of truth) :
 *  - statut, moteur par défaut et capacités affichés sont EXACTEMENT ceux
 *    renvoyés par le Core (GET /providers) : une capacité inconnue est rendue
 *    brute, jamais renommée ni inventée ;
 *  - « Définir par défaut » est une action Core (PUT /providers/{id}/default)
 *    suivie d'une relecture, sans aucun état local ;
 *  - cette surface est la SEULE à exposer le CRUD provider (le workspace
 *    Settings n'en duplique aucune action).
 *
 * Hooks Core mockés : ces tests valident le rendu et l'orchestration, pas le
 * ProviderManager (couvert côté backend).
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ProvidersWorkspace } from "@/components/features/providers/components/providers-workspace";
import { useProviders } from "@/components/features/providers/hooks/use-providers";
import type { Provider } from "@/lib/api/providers";

jest.mock("@/components/features/providers/hooks/use-providers", () => ({
	useProviders: jest.fn(),
}));

jest.mock("@/lib/api/providers", () => ({
	listProviders: jest.fn(async () => []),
	getProvider: jest.fn(),
	getProviderCatalog: jest.fn(async () => []),
	createProvider: jest.fn(),
	updateProvider: jest.fn(),
	deleteProvider: jest.fn(),
	testProvider: jest.fn(),
	setDefaultProvider: jest.fn(),
	listProviderModels: jest.fn(async () => []),
}));

jest.mock("@/lib/api/models", () => ({
	listModels: jest.fn(async () => []),
	toggleModel: jest.fn(),
}));

const refetch = jest.fn();
const setDefault = jest.fn();
const toggleEnabled = jest.fn();
const testConnection = jest.fn();
const deleteProviderAsync = jest.fn();
const createProviderAsync = jest.fn();
const updateProviderAsync = jest.fn();

/** Provider connecté, non défaut : capacités déclarées par le Core. */
const ollama: Provider = {
	id: "ollama",
	name: "Ollama",
	type: "ollama",
	enabled: true,
	status: "connected",
	default_model: "qwen2.5-coder",
	is_default: false,
	base_url: "http://127.0.0.1:11434",
	models: ["qwen2.5-coder", "llama3.2"],
	capabilities: ["llm", "vision", "embedding", "tool_calling"],
	has_api_key: true,
};

/** Provider hors ligne, moteur par défaut (is_default = état Core). */
const lmstudio: Provider = {
	id: "lmstudio",
	name: "LM Studio",
	type: "lmstudio",
	enabled: true,
	status: "disconnected",
	default_model: "qwen2.5",
	is_default: true,
	base_url: "http://127.0.0.1:1234",
	models: [],
	capabilities: ["llm"],
};

function setup(providers: Provider[], over: Record<string, unknown> = {}) {
	(useProviders as jest.Mock).mockReturnValue({
		providers,
		isLoading: false,
		error: null,
		refetch,
		isCreating: false,
		isUpdating: false,
		isDeleting: false,
		isTesting: false,
		testConnection,
		toggleEnabled,
		setDefault,
		deleteProviderAsync,
		createProviderAsync,
		updateProviderAsync,
		...over,
	});
}

function renderWorkspace() {
	const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
	return render(
		<QueryClientProvider client={client}>
			<ProvidersWorkspace />
		</QueryClientProvider>,
	);
}

beforeEach(() => {
	jest.clearAllMocks();
	setDefault.mockResolvedValue(undefined);
	refetch.mockResolvedValue(undefined);
	toggleEnabled.mockResolvedValue(undefined);
});

describe("ProvidersWorkspace — état Core affiché tel quel", () => {
	it("affiche les statuts et capacités renvoyés par le Core (valeur inconnue rendue brute)", () => {
		setup([ollama, lmstudio]);
		renderWorkspace();

		expect(screen.getByText("Connecté")).toBeInTheDocument();
		// « Hors ligne » existe aussi comme filtre de statut (bouton) : on ne
		// vérifie ici que le statut de carte (span), état réel du Core.
		expect(
			screen.getAllByText("Hors ligne").filter((el) => el.tagName === "SPAN"),
		).toHaveLength(1);

		// Capacités connues → libellé d'affichage ; l'inconnue reste brute.
		expect(screen.getAllByText("LLM")).toHaveLength(2);
		expect(screen.getByText("Vision")).toBeInTheDocument();
		expect(screen.getByText("Embeddings")).toBeInTheDocument();
		expect(screen.getByText("tool_calling")).toBeInTheDocument();
		expect(screen.getByText("Vision").getAttribute("title")).toBe(
			"Capacité déclarée par le Core : Vision",
		);
	});

	it("le badge de défaut provient de is_default, jamais d'un choix local", () => {
		setup([ollama, lmstudio]);
		renderWorkspace();

		expect(screen.getByText("Défaut")).toBeInTheDocument();
		expect(screen.getByText("Moteur par défaut")).toBeInTheDocument();
		// Un seul provider non-défaut → une seule action possible.
		expect(screen.getAllByRole("button", { name: "Définir par défaut" })).toHaveLength(1);
	});

	it("« Définir par défaut » appelle le Core puis relit l'état", async () => {
		setup([ollama, lmstudio]);
		renderWorkspace();

		fireEvent.click(screen.getByRole("button", { name: "Définir par défaut" }));

		await waitFor(() => expect(setDefault).toHaveBeenCalledWith("ollama"));
		expect(refetch).toHaveBeenCalled();
	});

	it("activation/désactivation déléguée au Core", async () => {
		setup([ollama, lmstudio]);
		renderWorkspace();

		fireEvent.click(screen.getAllByRole("button", { name: "Désactiver" })[0]);

		await waitFor(() => expect(toggleEnabled).toHaveBeenCalledWith("ollama", false));
	});
});

describe("ProvidersWorkspace — surface de gestion (CRUD) unique", () => {
	it("expose les actions CRUD (Ajouter / Tester / Configurer / Supprimer)", () => {
		setup([ollama, lmstudio]);
		renderWorkspace();

		expect(screen.getByRole("button", { name: /Ajouter un provider/ })).toBeInTheDocument();
		expect(screen.getAllByRole("button", { name: "Tester la connexion" })).toHaveLength(2);
		expect(screen.getAllByRole("button", { name: "Configurer" })).toHaveLength(2);
		expect(screen.getAllByRole("button", { name: "Supprimer" })).toHaveLength(2);
	});

	it("la recherche filtre l'affichage sans déclencher de mutation", () => {
		setup([ollama, lmstudio]);
		renderWorkspace();

		fireEvent.change(
			screen.getByPlaceholderText("Rechercher un provider (nom, type, URL)…"),
			{ target: { value: "studio" } },
		);

		expect(screen.getByText("LM Studio")).toBeInTheDocument();
		expect(screen.queryByText("Ollama")).toBeNull();
		expect(setDefault).not.toHaveBeenCalled();
		expect(toggleEnabled).not.toHaveBeenCalled();
		expect(deleteProviderAsync).not.toHaveBeenCalled();
	});

	it("états vides et erreurs explicites (aucune donnée inventée)", () => {
		setup([]);
		const { unmount } = renderWorkspace();
		expect(
			screen.getByText(
				"Aucun provider configuré. Cliquez sur « Ajouter un provider » pour commencer.",
			),
		).toBeInTheDocument();
		unmount();

		setup([], { error: "Connexion Core refusée" });
		renderWorkspace();
		expect(screen.getByText("Erreur : Connexion Core refusée")).toBeInTheDocument();
		expect(screen.queryByText("Ollama")).toBeNull();
	});
});

