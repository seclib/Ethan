/**
 * Tests WebUI — Settings → Providers : section « révélation seule ».
 *
 * Contrat d'architecture (AGENTS.md ; ADR-3002 providers source of truth) :
 * le CRUD provider (création, endpoint, clé API, activation, test, moteur et
 * modèle par défaut) vit EXCLUSIVEMENT dans le workspace /providers et les
 * endpoints Core (ProviderManager). La section Settings doit uniquement
 * RÉVÉLER l'état live (GET /providers) et pointer vers ce workspace : aucune
 * mutation, aucun formulaire, aucune logique dupliquée.
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { SettingsWorkspace } from "../../../src/components/features/settings/components/settings-workspace";
import {
	listProviders,
	createProvider,
	updateProvider,
	deleteProvider,
	testProvider,
	setDefaultProvider,
	type Provider,
} from "@/lib/api/providers";

// La section « General » fantôme (éditeur /v1/settings non consommé) a été
// supprimée — plus aucun mock de useSettings nécessaire.

jest.mock("@/lib/api/providers", () => ({
	listProviders: jest.fn(async () => []),
	createProvider: jest.fn(),
	updateProvider: jest.fn(),
	deleteProvider: jest.fn(),
	testProvider: jest.fn(),
	setDefaultProvider: jest.fn(),
}));

const ollama: Provider = {
	id: "ollama",
	name: "Ollama",
	type: "ollama",
	enabled: true,
	status: "connected",
	default_model: "qwen2.5-coder",
	is_default: false,
	base_url: "http://127.0.0.1:11434",
	models: [],
	capabilities: ["llm", "vision", "transcription", "tool_calling"],
};

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

function renderWorkspace() {
	const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
	return render(
		<QueryClientProvider client={client}>
			<SettingsWorkspace />
		</QueryClientProvider>,
	);
}

function openProvidersSection() {
	fireEvent.click(screen.getByRole("button", { name: "Providers" }));
	return screen.findByText("Fournisseurs réellement configurés dans le Core — état en temps réel");
}

beforeEach(() => {
	jest.clearAllMocks();
	(listProviders as jest.Mock).mockResolvedValue([ollama, lmstudio]);
});

describe("Settings → Providers — révélation seule (pas de second cerveau)", () => {
	it("la section est atteignable depuis le menu Settings", () => {
		renderWorkspace();
		expect(screen.getByRole("button", { name: "Providers" })).toBeInTheDocument();
	});

	it("révèle l'état live du Core (statuts, défaut, capacités telles quelles)", async () => {
		renderWorkspace();
		await openProvidersSection();

		// Providers réellement configurés côté Core (chargement async de GET /providers).
		expect(await screen.findByText("Ollama")).toBeInTheDocument();
		expect(screen.getByText("LM Studio")).toBeInTheDocument();
		// Moteur par défaut : état Core (is_default), pas un choix local.
		expect(screen.getByText("moteur par défaut")).toBeInTheDocument();
		expect(
			screen.getByText(/Moteur actif : LM Studio — défini par le Core/),
		).toBeInTheDocument();
		// Capacités connues → libellé ; inconnue → valeur brute du Core.
		expect(screen.getAllByText("LLM")).toHaveLength(2);
		expect(screen.getByText("Vision")).toBeInTheDocument();
		expect(screen.getByText("Transcription")).toBeInTheDocument();
		expect(screen.getByText("tool_calling")).toBeInTheDocument();
	});

	it("ne duplique aucune action de gestion : lecture seule, zéro mutation", async () => {
		renderWorkspace();
		await openProvidersSection();

		// Actions du workspace absentes de la section Settings.
		expect(screen.queryByRole("button", { name: /Ajouter un provider/ })).toBeNull();
		expect(screen.queryByRole("button", { name: /Tester la connexion/ })).toBeNull();
		expect(screen.queryByRole("button", { name: "Définir par défaut" })).toBeNull();
		expect(screen.queryByRole("button", { name: "Configurer" })).toBeNull();
		expect(screen.queryByRole("button", { name: "Supprimer" })).toBeNull();

		// Aucun champ de saisie DANS LA SECTION : la section ne configure rien.
		// (Le champ de recherche de la rail de navigation — présentation seule —
		// est hors périmètre : on scope au panneau de contenu.)
		const content = screen.getByTestId("settings-section-content");
		expect(content.querySelectorAll("input, select, textarea")).toHaveLength(0);

		// Seule la lecture est appelée — aucune écriture Core.
		expect(listProviders).toHaveBeenCalled();
		expect(createProvider).not.toHaveBeenCalled();
		expect(updateProvider).not.toHaveBeenCalled();
		expect(deleteProvider).not.toHaveBeenCalled();
		expect(testProvider).not.toHaveBeenCalled();
		expect(setDefaultProvider).not.toHaveBeenCalled();
	});

	it("renvoie vers la surface de gestion unique : /providers", async () => {
		renderWorkspace();
		await openProvidersSection();

		const link = screen.getByText("Ouvrir le workspace Providers").closest("a");
		expect(link?.getAttribute("href")).toBe("/providers");
	});

	it("sans provider configuré : message explicite, aucun provider inventé", async () => {
		(listProviders as jest.Mock).mockResolvedValue([]);
		renderWorkspace();
		await openProvidersSection();

		expect(
			await screen.findByText(
				"Aucun provider configuré. Ajoutez-le depuis le workspace Providers.",
			),
		).toBeInTheDocument();
		expect(screen.queryByText("Ollama")).toBeNull();
	});
});

