/**
 * Tests — recherche de sections dans Settings (navigation guidée).
 *
 * Contexte : l'état `search` du SettingsWorkspace était déclaré mais jamais
 * consommé (code mort) alors que le menu compte 24 sections réparties sur 8
 * groupes. Il est désormais câblé en filtre de présentation (aucune logique
 * métier : filtre sur les libellés de la taxinomie `settings-nav`).
 *
 * Garde-fous :
 *  - la recherche filtre les sections (libellé, casse-insensible) ;
 *  - un état vide explicite est affiché quand rien ne correspond ;
 *  - vider la recherche restaure l'arborescence complète ;
 *  - pendant une recherche, l'en-tête de groupe situe le résultat sans
 *    réintroduire de doublon en-tête/item (« Skills › Skills »).
 */
import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SettingsWorkspace } from "../../../src/components/features/settings/components/settings-workspace";

// La section « General » fantôme (draft /v1/settings) a été supprimée du
// workspace — le render par défaut monte la section Chat (préférences réelles).

function renderWorkspace() {
	const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
	return render(
		<QueryClientProvider client={client}>
			<SettingsWorkspace />
		</QueryClientProvider>,
	);
}

function searchBox() {
	return screen.getByRole("textbox", { name: "Rechercher une section Settings" });
}

describe("Settings — recherche de sections", () => {
	it("filtre les sections par libellé (insensible à la casse)", () => {
		renderWorkspace();
		expect(screen.getByRole("button", { name: "Appearance" })).toBeTruthy();

		fireEvent.change(searchBox(), { target: { value: "rag" } });

		// RAG correspond, Appearance est masqué.
		expect(screen.getByRole("button", { name: "RAG" })).toBeTruthy();
		expect(screen.queryByRole("button", { name: "Appearance" })).toBeNull();
	});

	it("affiche un état vide explicite quand aucune section ne correspond", () => {
		renderWorkspace();
		fireEvent.change(searchBox(), { target: { value: "zzzz" } });

		expect(screen.getByText(/Aucune section ne correspond/)).toBeTruthy();
		expect(screen.queryByRole("button", { name: "RAG" })).toBeNull();
	});

	it("restaure l'arborescence complète quand la recherche est vidée", () => {
		renderWorkspace();
		fireEvent.change(searchBox(), { target: { value: "rag" } });
		expect(screen.queryByRole("button", { name: "Appearance" })).toBeNull();

		fireEvent.change(searchBox(), { target: { value: "" } });

		expect(screen.getByRole("button", { name: "Appearance" })).toBeTruthy();
		expect(screen.getByRole("button", { name: "RAG" })).toBeTruthy();
	});

	it("pendant une recherche, l'en-tête de groupe situe le résultat (sans doublon en-tête/item)", () => {
		renderWorkspace();
		// « RAG » appartient au groupe Knowledge : l'en-tête doit apparaître
		// (le groupe à section unique est normalement rendu sans en-tête).
		fireEvent.change(searchBox(), { target: { value: "rag" } });
		expect(screen.getByText("Knowledge")).toBeTruthy();

		// « Skills » : groupe mono-section dont l'item porte le même libellé —
		// pas de doublon « Skills › Skills » même en recherche.
		fireEvent.change(searchBox(), { target: { value: "skills" } });
		expect(screen.getAllByText("Skills")).toHaveLength(1);
	});
});
