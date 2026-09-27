/**
 * Tests — Les choix de configuration du moteur RAG viennent du Core.
 *
 * Règle AGENTS.md / principe « single source of truth » : aucune interface ne
 * duplique les listes de capacités du Core.
 *  - le sélecteur de backend vectoriel rend `config.vector_backends`
 *    (source : `SUPPORTED_VECTOR_BACKENDS`, core/rag/vector_store.py) ;
 *  - le sélecteur de stratégie de découpage rend `config.splitting_strategies`
 *    (source : `SPLITTING_STRATEGIES`, core/rag/ingestion.py) ;
 *  - les libellés locaux ne sont que de l'affichage : une valeur inconnue est
 *    rendue brute, une valeur portée disparue du Core reste sélectionnable ;
 *  - les suggestions d'embedding viennent du catalogue Core (`GET /models`)
 *    filtré sur la capacité réellement déclarée « embedding ».
 */
import * as React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
	ChunkingSection,
	EmbeddingsSection,
	VectorDatabaseSection,
} from "../../../src/components/features/settings/components/settings-ai-sections";

/** Payload `GET /v1/rag/config` — réaffectable par les tests. */
let mockRagPayload: Record<string, any> = {
	config: {
		chunk_size: 512,
		chunk_overlap: 64,
		top_k: 4,
		max_context_chars: 4000,
		embedding_model: "nomic-embed-text",
		strategy: "auto",
		splitting_strategy: "character",
		// Le Core n'expose plus « paragraph » : l'UI ne doit pas le réinventer.
		splitting_strategies: ["character", "sentence"],
		vector_backend: "memory",
		// Le Core n'expose plus « qdrant » : idem.
		vector_backends: ["memory", "chromadb"],
		vector_backend_config: { url: "" },
	},
	stats: {
		documents: 12,
		chunks: 340,
		embedding_mode: "llm",
		indexed_embeddings: true,
		embedding_model: "nomic-embed-text",
		strategy: "auto",
		strategies: [],
	},
};

jest.mock("@/lib/api/rag", () => ({
	getRagConfig: jest.fn(async () => mockRagPayload),
	getRagStatus: jest.fn(async () => mockRagPayload.stats),
	updateRagConfig: jest.fn(async () => mockRagPayload),
}));

jest.mock("@/lib/api/models", () => ({
	listModels: jest.fn(async () => [
		{ id: "m-embed", model: "nomic-embed-text", provider: "ollama", capabilities: ["embedding"] },
		{ id: "m-llm", model: "llama3.1:8b", provider: "ollama", capabilities: ["llm"] },
	]),
}));

function renderSection(section: React.ReactElement) {
	const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
	return render(<QueryClientProvider client={client}>{section}</QueryClientProvider>);
}

function optionValues(container: HTMLElement): string[] {
	return Array.from(container.querySelectorAll("option")).map((o) => (o as HTMLOptionElement).value);
}

beforeEach(() => {
	mockRagPayload = {
		...mockRagPayload,
		config: {
			...mockRagPayload.config,
			splitting_strategy: "character",
			splitting_strategies: ["character", "sentence"],
			vector_backend: "memory",
			vector_backends: ["memory", "chromadb"],
		},
	};
});

describe("Knowledge/RAG — les choix sont pilotés par le Core", () => {
	it("backend vectoriel : seules les valeurs du Core sont proposées", async () => {
		const { container } = renderSection(<VectorDatabaseSection />);
		await waitFor(() => expect(optionValues(container)).toEqual(["memory", "chromadb"]));
		// « qdrant » est pourtant un libellé connu de l'UI : il ne doit PAS
		// réapparaître si le Core ne le déclare plus.
		expect(screen.queryByText("Qdrant")).toBeNull();
		// Libellé d'affichage appliqué aux valeurs connues.
		expect(screen.getByText("ChromaDB")).toBeTruthy();
	});

	it("backend vectoriel : la valeur courante retirée du Core reste sélectionnable", async () => {
		mockRagPayload = {
			...mockRagPayload,
			config: { ...mockRagPayload.config, vector_backend: "weaviate" },
		};
		const { container } = renderSection(<VectorDatabaseSection />);
		await waitFor(() => expect(optionValues(container)).toContain("weaviate"));
		expect(optionValues(container)).toEqual(["memory", "chromadb", "weaviate"]);
		// Valeur inconnue : rendue brute, sans libellé inventé.
		const labels = Array.from(container.querySelectorAll("option")).map((o) =>
			(o as HTMLOptionElement).textContent?.trim(),
		);
		expect(labels).toContain("weaviate");
	});

	it("découpage : seules les stratégies implémentées par le Core sont proposées", async () => {
		const { container } = renderSection(<ChunkingSection />);
		await waitFor(() => expect(optionValues(container)).toEqual(["character", "sentence"]));
		expect(screen.queryByText("Paragraphes")).toBeNull();
		expect(screen.getByText("Caractères")).toBeTruthy();
	});

	it("découpage : stratégie absente du Core et valeur inconnue rendue brute", async () => {
		mockRagPayload = {
			...mockRagPayload,
			config: { ...mockRagPayload.config, splitting_strategy: "semantic" },
		};
		const { container } = renderSection(<ChunkingSection />);
		await waitFor(() => expect(optionValues(container)).toContain("semantic"));
		expect(optionValues(container)).toEqual(["character", "sentence", "semantic"]);
		expect(screen.getByText("semantic")).toBeTruthy();
	});

	it("embedding : les suggestions viennent du catalogue Core filtré sur la capacité", async () => {
		const { container } = renderSection(<EmbeddingsSection />);
		await waitFor(() =>
			expect(container.querySelector("#embedding-model-suggestions")).toBeTruthy(),
		);
		const suggestions = Array.from(
			container.querySelectorAll("#embedding-model-suggestions option"),
		).map((o) => (o as HTMLOptionElement).value);
		expect(suggestions).toEqual(["nomic-embed-text"]);
		// Le modèle sans capacité « embedding » ne doit jamais être suggéré.
		expect(suggestions).not.toContain("llama3.1:8b");
		// L'appel passe explicitement include_custom : les modèles déclarés par
		// l'utilisateur dans le Core doivent être suggérés aussi.
		const modelsApi = jest.requireMock("@/lib/api/models") as { listModels: jest.Mock };
		expect(modelsApi.listModels).toHaveBeenCalledWith({ include_custom: true });
	});
});
