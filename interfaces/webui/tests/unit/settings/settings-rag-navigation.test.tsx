/**
 * Tests — Restauration de la section Settings → RAG (first-class).
 *
 * Régression couverte : `RagSection` existait dans settings-workspace.tsx
 * mais n'était plus référencée (type `Section`, tableau `SECTIONS` et dispatch
 * conditionnel) — le formulaire du moteur RAG était du code mort inaccessible.
 *
 * Garde-fous :
 *  - l'entrée « RAG » est visible dans le menu Settings ;
 *  - la section rend le formulaire du moteur (paramètres réellement supportés
 *    par le backend : chunking, top_k, borne de contexte, embedding, stratégie) ;
 *  - Knowledge reste la gestion des données (collections) avec un lien
 *    secondaire « Configurer le moteur RAG » vers #rag ;
 *  - Knowledge et RAG restent deux sections distinctes.
 */
import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SettingsWorkspace } from "../../../src/components/features/settings/components/settings-workspace";

// Section General montée par défaut au render du workspace.
// ⚠️ Références STABLES : le composant re-seed son draft via un effet [settings] —
// un objet recréé à chaque render déclencherait une boucle infinie de renders.
jest.mock("@/components/features/settings/hooks/use-settings", () => {
	const stableSettings = { system: {}, llm: {} };
	const stableUpdate = async () => ({});
	return {
		useSettings: () => ({
			settings: stableSettings,
			isLoading: false,
			update: stableUpdate,
			isUpdating: false,
		}),
	};
});

const ragPayload = {
	config: {
		chunk_size: 512,
		chunk_overlap: 64,
		top_k: 4,
		max_context_chars: 4000,
		embedding_model: "nomic-embed-text",
		strategy: "auto",
	},
	stats: {
		documents: 12,
		chunks: 340,
		embedding_mode: "llm",
		indexed_embeddings: true,
		embedding_model: "nomic-embed-text",
		strategy: "auto",
		strategies: [
			{ id: "auto", label: "Auto", description: "Choix automatique", requires_embeddings: false },
		],
		recommendation: { strategy_id: "auto", reason: "Capacités réelles détectées", has_real_embeddings: true },
	},
};

jest.mock("@/lib/api/rag", () => ({
	getRagConfig: jest.fn(async () => ragPayload),
	getRagStrategies: jest.fn(async () => ({
		default: "auto",
		strategies: ragPayload.stats.strategies,
		recommendation: ragPayload.stats.recommendation,
	})),
	getRagStatus: jest.fn(async () => ragPayload.stats),
	updateRagConfig: jest.fn(async () => ragPayload),
}));

function renderWorkspace() {
	const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
	return render(
		<QueryClientProvider client={client}>
			<SettingsWorkspace />
		</QueryClientProvider>,
	);
}

describe("Settings → RAG — section first-class restaurée", () => {
	it("affiche l'entrée RAG dans le menu Settings", () => {
		renderWorkspace();
		expect(screen.getByRole("button", { name: /RAG/ })).toBeTruthy();
	});

	it("ouvre la section RAG avec le formulaire du moteur (paramètres réellement supportés)", async () => {
		renderWorkspace();
		fireEvent.click(screen.getByRole("button", { name: /RAG/ }));

		expect(
			await screen.findByText("Configuration du moteur d'ingestion et de récupération"),
		).toBeTruthy();
		expect(screen.getByText("Top K")).toBeTruthy();
		expect(screen.getByText("Chunk size")).toBeTruthy();
		expect(screen.getByText("Chunk overlap")).toBeTruthy();
		expect(screen.getByText("Contexte max (caractères)")).toBeTruthy();
		expect(screen.getByText(/Modèle d/)).toBeTruthy(); // Modèle d'embedding
		expect(screen.getByRole("button", { name: /Enregistrer/ })).toBeTruthy();
	});

	it("expose la stratégie de recherche fournie par le Core (aucune stratégie inventée côté UI)", async () => {
		renderWorkspace();
		fireEvent.click(screen.getByRole("button", { name: /RAG/ }));

		const select = (await screen.findByText("Stratégie de recherche")).parentElement?.querySelector("select");
		expect(select).toBeTruthy();
		expect(select?.value).toBe("auto");
		expect(screen.getByText("Recommandation ETHAN :")).toBeTruthy();
	});

	it("Knowledge conserve la gestion des données avec un lien secondaire vers le moteur RAG", async () => {
		renderWorkspace();
		fireEvent.click(screen.getByRole("button", { name: /Knowledge/ }));

		expect(await screen.findByText("Ouvrir le workspace Knowledge")).toBeTruthy();
		const link = screen.getByText("Configurer le moteur RAG").closest("a");
		expect(link?.getAttribute("href")).toBe("#rag");
	});

	it("navigue vers RAG via le hash #rag (accès direct URL / refresh)", async () => {
		renderWorkspace();
		fireEvent.click(screen.getByRole("button", { name: /Knowledge/ }));
		expect(await screen.findByText("Ouvrir le workspace Knowledge")).toBeTruthy();

		// jsdom n'implémente pas la navigation par clic d'ancre : on simule
		// exactement le scénario « accès direct par URL » que le composant
		// supporte (listener hashchange → applyHash → lookup SECTIONS).
		window.location.hash = "rag";
		fireEvent(window, new Event("hashchange"));

		expect(
			await screen.findByText("Configuration du moteur d'ingestion et de récupération"),
		).toBeTruthy();
	});
});
