/**
 * Tests — Settings → Search : console de recherche globale du Core.
 *
 * Contrat (audit anti-fantôme 2026-09-30) : la section Search interroge le
 * moteur réel (`/v1/search` + `/v1/search/types`). Les préférences inventées
 * (Default Search Type, Results Limit, Fuzzy Matching) ont été supprimées.
 */
import * as React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockSearch = jest.fn();
const mockTypes = jest.fn();

jest.mock("@/lib/api/search", () => ({
  search: (...args: unknown[]) => mockSearch(...args),
  listSearchTypes: (...args: unknown[]) => mockTypes(...args),
}));

import { SearchSection } from "../../../src/components/features/settings/components/settings-sections";

function renderSection() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <SearchSection />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  mockSearch.mockReset();
  mockTypes.mockReset();
  mockTypes.mockResolvedValue({ types: ["web", "knowledge", "library", "conversation"] });
});

describe("Settings → Search (console Core)", () => {
  it("état initial : aucune requête tant que l'utilisateur n'a rien soumis", async () => {
    renderSection();

    expect(screen.getByText(/Saisissez une requête/)).toBeInTheDocument();
    await waitFor(() => expect(mockTypes).toHaveBeenCalled());
    expect(mockSearch).not.toHaveBeenCalled();
  });

  it("soumettre une requête interroge le Core et affiche les résultats réels", async () => {
    mockSearch.mockResolvedValue({
      query: "agents",
      type: "knowledge",
      total: 1,
      results: [
        { id: "k-1", title: "Architecture agents", type: "knowledge", source: "docs/agents.md" },
      ],
    });
    renderSection();

    fireEvent.change(screen.getByLabelText("Requête de recherche"), {
      target: { value: "agents" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Rechercher" }));

    await waitFor(() =>
      expect(mockSearch).toHaveBeenCalledWith("agents", "knowledge", 20),
    );
    expect(await screen.findByText("Architecture agents")).toBeInTheDocument();
    expect(screen.getByText(/1 résultat\(s\) pour « agents »/)).toBeInTheDocument();
  });

  it("aucun résultat : état vide explicite", async () => {
    mockSearch.mockResolvedValue({ query: "zzz", type: "knowledge", total: 0, results: [] });
    renderSection();

    fireEvent.change(screen.getByLabelText("Requête de recherche"), { target: { value: "zzz" } });
    fireEvent.click(screen.getByRole("button", { name: "Rechercher" }));

    expect(await screen.findByText("Aucun résultat.")).toBeInTheDocument();
  });

  it("le type sélectionné est transmis au Core (conversation)", async () => {
    mockSearch.mockResolvedValue({ query: "chat", type: "conversation", total: 0, results: [] });
    renderSection();

    fireEvent.change(screen.getByLabelText("Type de recherche"), {
      target: { value: "conversation" },
    });
    fireEvent.change(screen.getByLabelText("Requête de recherche"), { target: { value: "chat" } });
    fireEvent.click(screen.getByRole("button", { name: "Rechercher" }));

    await waitFor(() => expect(mockSearch).toHaveBeenCalledWith("chat", "conversation", 20));
  });

  it("erreur Core : état d'erreur explicite (aucun résultat simulé)", async () => {
    mockSearch.mockRejectedValue(new Error("core indisponible"));
    renderSection();

    fireEvent.change(screen.getByLabelText("Requête de recherche"), { target: { value: "x" } });
    fireEvent.click(screen.getByRole("button", { name: "Rechercher" }));

    expect(await screen.findByText(/Recherche impossible/)).toBeInTheDocument();
  });

  it("n'expose plus les préférences fantômes (Limit, Fuzzy Matching)", () => {
    renderSection();

    expect(screen.queryByText(/Search Results Limit/i)).toBeNull();
    expect(screen.queryByText(/Fuzzy Matching/i)).toBeNull();
    expect(screen.queryByText(/Default Search Type/i)).toBeNull();
  });
});
