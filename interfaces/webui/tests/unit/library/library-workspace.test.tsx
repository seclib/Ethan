import * as React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests de la page Library (/library) — contrat d'interface uniquement.
 *
 * Convention du repo : le VRAI @tanstack/react-query est utilisé (provider par
 * test) ; seul le client API (@/lib/api/library) est mocké — le test contrôle
 * ce que le Core renvoie, jamais l'HTTP.
 *
 * Invariants d'interface (règle AGENTS.md) : la Library AFFICHE les ressources
 * exposées par le Core (documents RAG, Knowledge, collections, images) — aucun
 * registre parallèle, aucune donnée simulée. Les états vide et erreur sont
 * explicites, et les filtres/recherche sont délégués au Core (filtres passés).
 */

const mockGetLibrary = jest.fn();
jest.mock("@/lib/api/library", () => ({
  getLibrary: (...args: unknown[]) => mockGetLibrary(...args),
}));

// Import APRÈS les mocks.
import { LibraryWorkspace } from "@/components/features/library/library-workspace";
import type { LibraryItem } from "@/lib/api/library";

function makeItem(over: Partial<LibraryItem> = {}): LibraryItem {
  return {
    id: "doc-1",
    title: "RFC 001",
    type: "document",
    created_at: "2026-01-02T03:04:05.000Z",
    ...over,
  };
}

function renderLibrary() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <LibraryWorkspace />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  mockGetLibrary.mockReset();
});

describe("LibraryWorkspace — états honnêtes", () => {
  it("bibliothèque vide : état vide nommant les sources Core", async () => {
    mockGetLibrary.mockResolvedValue({ items: [], total: 0, filters: {} });

    renderLibrary();

    expect(
      await screen.findByText("Aucun élément dans la bibliothèque"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/exposés par ETHAN Core apparaîtront ici/),
    ).toBeInTheDocument();
  });

  it("erreur : message explicite + Réessayer relance la requête", async () => {
    mockGetLibrary
      .mockRejectedValueOnce(new Error("core indisponible"))
      .mockResolvedValue({ items: [], total: 0, filters: {} });

    renderLibrary();

    expect(
      await screen.findByText("Impossible de charger la bibliothèque"),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Réessayer" }));

    await waitFor(() => expect(mockGetLibrary).toHaveBeenCalledTimes(2));
    expect(
      await screen.findByText("Aucun élément dans la bibliothèque"),
    ).toBeInTheDocument();
  });
});

describe("LibraryWorkspace — affichage des ressources du Core", () => {
  it("affiche les éléments renvoyés et le compteur (pluriel)", async () => {
    mockGetLibrary.mockResolvedValue({
      items: [
        makeItem(),
        makeItem({ id: "k-1", title: "Mémoire projet", type: "knowledge" }),
      ],
      total: 2,
      filters: {},
    });

    renderLibrary();

    expect(await screen.findByText("2 éléments")).toBeInTheDocument();
    expect(screen.getByText("RFC 001")).toBeInTheDocument();
    expect(screen.getByText("Mémoire projet")).toBeInTheDocument();
  });

  it("un seul élément : compteur au singulier", async () => {
    mockGetLibrary.mockResolvedValue({
      items: [makeItem()],
      total: 1,
      filters: {},
    });

    renderLibrary();

    expect(await screen.findByText("1 élément")).toBeInTheDocument();
  });

  it("sélection : détail avec contenu et métadonnées réels", async () => {
    mockGetLibrary.mockResolvedValue({
      items: [
        makeItem({ content: "contenu réel", metadata: { source: "rfc" } }),
      ],
      total: 1,
      filters: {},
    });

    renderLibrary();

    fireEvent.click(await screen.findByText("RFC 001"));

    expect(screen.getByText("Contenu")).toBeInTheDocument();
    expect(screen.getByText("contenu réel")).toBeInTheDocument();
    expect(screen.getByText("Métadonnées")).toBeInTheDocument();
  });
});

describe("LibraryWorkspace — filtres délégués au Core", () => {
  it("filtre par type transmis dans la requête", async () => {
    mockGetLibrary.mockResolvedValue({ items: [], total: 0, filters: {} });

    renderLibrary();
    await screen.findByText("Aucun élément dans la bibliothèque");

    fireEvent.click(screen.getByRole("button", { name: "Collections" }));

    await waitFor(() =>
      expect(mockGetLibrary).toHaveBeenLastCalledWith(
        expect.objectContaining({ type: "collection" }),
      ),
    );
  });

  it("recherche transmise dans la requête (aucun filtrage local simulé en plus)", async () => {
    mockGetLibrary.mockResolvedValue({ items: [], total: 0, filters: {} });

    renderLibrary();
    await screen.findByText("Aucun élément dans la bibliothèque");

    fireEvent.change(
      screen.getByPlaceholderText("Rechercher dans la bibliothèque…"),
      { target: { value: "rfc" } },
    );

    await waitFor(() =>
      expect(mockGetLibrary).toHaveBeenLastCalledWith(
        expect.objectContaining({ search: "rfc" }),
      ),
    );
  });
});
