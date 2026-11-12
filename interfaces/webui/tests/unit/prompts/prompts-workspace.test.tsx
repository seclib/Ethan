import * as React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests de la page Prompts (/prompts) — contrat d'interface uniquement.
 *
 * Les prompts vivent dans ETHAN Core (PromptManager) : le test mocke le client
 * API (@/lib/api/prompts) et vérifie l'affichage réel, la création, l'édition,
 * la suppression confirmée et le filtre local (présentation seule — le Core
 * n'expose pas d'endpoint de recherche pour les prompts).
 */

const mockList = jest.fn();
const mockCreate = jest.fn();
const mockUpdate = jest.fn();
const mockDelete = jest.fn();

jest.mock("@/lib/api/prompts", () => ({
  listPrompts: (...a: unknown[]) => mockList(...a),
  createPrompt: (...a: unknown[]) => mockCreate(...a),
  updatePrompt: (...a: unknown[]) => mockUpdate(...a),
  deletePrompt: (...a: unknown[]) => mockDelete(...a),
}));

const mockAddToast = jest.fn();
jest.mock("@/store/ui.store", () => ({
  useUIStore: (selector?: (s: { addToast: typeof mockAddToast }) => unknown) => {
    const state = { addToast: mockAddToast };
    return selector ? selector(state) : state;
  },
}));

// Imports APRÈS les mocks.
import { PromptsWorkspace } from "@/components/features/prompts/prompts-workspace";
import type { Prompt } from "@/lib/api/prompts";

function makePrompt(over: Partial<Prompt> = {}): Prompt {
  return {
    id: "p1",
    name: "revue de code",
    text: "Relis ce diff et propose des améliorations.",
    description: "Revue systématique",
    tags: ["code"],
    metadata: {},
    created_at: "2026-01-01T09:00:00.000Z",
    ...over,
  };
}

function renderWorkspace() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <PromptsWorkspace />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("PromptsWorkspace — états honnêtes", () => {
  it("aucun prompt : état vide nommant le Core", async () => {
    mockList.mockResolvedValue([]);

    renderWorkspace();

    expect(await screen.findByText("Aucun prompt")).toBeInTheDocument();
    expect(screen.getByText(/persistés par ETHAN Core/)).toBeInTheDocument();
  });

  it("erreur Core : message explicite + Réessayer relance", async () => {
    mockList.mockRejectedValueOnce(new Error("core indisponible")).mockResolvedValue([]);

    renderWorkspace();

    expect(await screen.findByText("Impossible de charger les prompts")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Réessayer" }));

    await waitFor(() => expect(mockList).toHaveBeenCalledTimes(2));
  });
});

describe("PromptsWorkspace — affichage et filtre local", () => {
  it("affiche contenu, description, tags et compteur", async () => {
    mockList.mockResolvedValue([
      makePrompt(),
      makePrompt({
        id: "p2",
        name: "veille",
        description: "Veille technologique",
        text: "Résume les nouveautés du jour.",
        tags: [],
      }),
    ]);

    renderWorkspace();

    expect(await screen.findByText("revue de code")).toBeInTheDocument();
    expect(screen.getByText("Revue systématique")).toBeInTheDocument();
    expect(screen.getByText("Relis ce diff et propose des améliorations.")).toBeInTheDocument();
    expect(screen.getByText("code")).toBeInTheDocument();
    expect(screen.getByText("2 prompts")).toBeInTheDocument();
  });

  it("le filtre local restreint la liste affichée (présentation seule)", async () => {
    mockList.mockResolvedValue([makePrompt(), makePrompt({ id: "p2", name: "veille" })]);

    renderWorkspace();
    await screen.findByText("revue de code");

    fireEvent.change(screen.getByPlaceholderText("Filtrer les prompts…"), {
      target: { value: "veille" },
    });

    expect(screen.queryByText("revue de code")).not.toBeInTheDocument();
    expect(screen.getByText("veille")).toBeInTheDocument();
    expect(screen.getByText("1 prompt")).toBeInTheDocument();
    // Le filtre est purement visuel : le Core n'est pas rappelé pour filtrer.
    expect(mockList).toHaveBeenCalledTimes(1);
  });
});

describe("PromptsWorkspace — écritures = appels Core", () => {
  it("création : champs et tags parsés transmis au Core", async () => {
    mockList.mockResolvedValue([]);
    mockCreate.mockResolvedValue(makePrompt({ name: "Traduction" }));

    renderWorkspace();
    await screen.findByText("Aucun prompt");

    fireEvent.click(screen.getByRole("button", { name: /Nouveau prompt/ }));
    fireEvent.change(screen.getByPlaceholderText("ex: revue de code"), {
      target: { value: "Traduction" },
    });
    fireEvent.change(screen.getByPlaceholderText("code, revue"), {
      target: { value: "langue, doc" },
    });
    const textarea = screen
      .getAllByRole("textbox")
      .find((el) => el.tagName === "TEXTAREA") as HTMLElement;
    fireEvent.change(textarea, { target: { value: "Traduis ce texte." } });
    fireEvent.click(screen.getByRole("button", { name: "Créer" }));

    await waitFor(() =>
      expect(mockCreate).toHaveBeenCalledWith({
        name: "Traduction",
        description: "",
        text: "Traduis ce texte.",
        tags: ["langue", "doc"],
      }),
    );
  });

  it("édition : PUT sur l'id du prompt", async () => {
    mockList.mockResolvedValue([makePrompt()]);
    mockUpdate.mockResolvedValue(makePrompt({ name: "revue v2" }));

    renderWorkspace();
    await screen.findByText("revue de code");

    fireEvent.click(screen.getByRole("button", { name: "Modifier" }));
    fireEvent.change(screen.getByPlaceholderText("ex: revue de code"), {
      target: { value: "revue v2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    await waitFor(() =>
      expect(mockUpdate).toHaveBeenCalledWith("p1", {
        name: "revue v2",
        description: "Revue systématique",
        text: "Relis ce diff et propose des améliorations.",
        tags: ["code"],
      }),
    );
  });

  it("suppression : confirmation explicite puis DELETE Core", async () => {
    mockList.mockResolvedValue([makePrompt()]);
    mockDelete.mockResolvedValue({ status: "deleted" });

    renderWorkspace();
    await screen.findByText("revue de code");

    fireEvent.click(screen.getByRole("button", { name: /Supprimer/ }));
    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Supprimer" }));

    await waitFor(() => expect(mockDelete).toHaveBeenCalledWith("p1"));
  });
});
