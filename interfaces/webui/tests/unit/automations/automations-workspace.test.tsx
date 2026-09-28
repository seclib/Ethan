import * as React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests de la page Automations (/automations) — contrat d'interface uniquement.
 *
 * Convention du repo : VRAI @tanstack/react-query, seul le client API
 * (@/lib/api/automations) est mocké — le test contrôle ce que le Core renvoie.
 * Invariants : états vide/erreur honnêtes, filtre délégué au Core (`?enabled=`),
 * déclenchement = POST Core (aucune exécution locale), confirmation avant
 * suppression.
 */

const mockList = jest.fn();
const mockCreate = jest.fn();
const mockUpdate = jest.fn();
const mockDelete = jest.fn();
const mockTrigger = jest.fn();

jest.mock("@/lib/api/automations", () => ({
  listAutomations: (...a: unknown[]) => mockList(...a),
  createAutomation: (...a: unknown[]) => mockCreate(...a),
  updateAutomation: (...a: unknown[]) => mockUpdate(...a),
  deleteAutomation: (...a: unknown[]) => mockDelete(...a),
  triggerAutomation: (...a: unknown[]) => mockTrigger(...a),
}));

const mockAddToast = jest.fn();
jest.mock("@/store/ui.store", () => ({
  useUIStore: (selector?: (s: { addToast: typeof mockAddToast }) => unknown) => {
    const state = { addToast: mockAddToast };
    return selector ? selector(state) : state;
  },
}));

// Imports APRÈS les mocks.
import { AutomationsWorkspace } from "@/components/features/automations/automations-workspace";
import type { Automation } from "@/lib/api/automations";

function makeRule(over: Partial<Automation> = {}): Automation {
  return {
    id: "a1",
    name: "Résumé quotidien",
    description: "Chaque matin",
    trigger: { type: "manual" },
    actions: [{ type: "notify" }],
    enabled: true,
    last_triggered_at: null,
    trigger_count: 0,
    metadata: {},
    created_at: "2026-01-01T00:00:00.000Z",
    updated_at: "2026-01-01T00:00:00.000Z",
    ...over,
  };
}

function renderWorkspace() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AutomationsWorkspace />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("AutomationsWorkspace — états honnêtes", () => {
  it("aucune règle : état vide nommant le Core", async () => {
    mockList.mockResolvedValue([]);

    renderWorkspace();

    expect(await screen.findByText("Aucune automation")).toBeInTheDocument();
    expect(screen.getByText(/stockées par ETHAN Core/)).toBeInTheDocument();
  });

  it("erreur Core : message explicite + Réessayer relance", async () => {
    mockList.mockRejectedValueOnce(new Error("core indisponible")).mockResolvedValue([]);

    renderWorkspace();

    expect(await screen.findByText("Impossible de charger les automations")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Réessayer" }));

    await waitFor(() => expect(mockList).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Aucune automation")).toBeInTheDocument();
  });
});

describe("AutomationsWorkspace — rendu des règles du Core", () => {
  it("affiche nom, compteur et état réel", async () => {
    mockList.mockResolvedValue([
      makeRule(),
      makeRule({
        id: "a2",
        name: "Veille",
        enabled: false,
        trigger_count: 3,
        last_triggered_at: "2026-02-01T10:00:00.000Z",
      }),
    ]);

    renderWorkspace();

    expect(await screen.findByText("Résumé quotidien")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
    expect(screen.getByText(/3 déclenchements/)).toBeInTheDocument();
    expect(screen.getByText("2 règles")).toBeInTheDocument();
  });

  it("le filtre Actives est délégué au Core (?enabled=true)", async () => {
    mockList.mockResolvedValue([]);

    renderWorkspace();
    await screen.findByText("Aucune automation");

    fireEvent.click(screen.getByRole("button", { name: "Actives" }));

    await waitFor(() => expect(mockList).toHaveBeenLastCalledWith(true));
  });

  it("règle inactive : déclenchement impossible (aucun POST)", async () => {
    mockList.mockResolvedValue([makeRule({ enabled: false })]);

    renderWorkspace();

    expect(await screen.findByRole("button", { name: /Déclencher/ })).toBeDisabled();
  });
});

describe("AutomationsWorkspace — actions = appels Core", () => {
  it("déclencher une règle active appelle le trigger du Core", async () => {
    mockList.mockResolvedValue([makeRule()]);
    mockTrigger.mockResolvedValue(makeRule({ trigger_count: 1 }));

    renderWorkspace();

    fireEvent.click(await screen.findByRole("button", { name: /Déclencher/ }));

    await waitFor(() => expect(mockTrigger).toHaveBeenCalledWith("a1"));
  });

  it("désactiver envoie `enabled: false` au Core", async () => {
    mockList.mockResolvedValue([makeRule()]);
    mockUpdate.mockResolvedValue(makeRule({ enabled: false }));

    renderWorkspace();

    fireEvent.click(await screen.findByRole("button", { name: /Désactiver/ }));

    await waitFor(() => expect(mockUpdate).toHaveBeenCalledWith("a1", { enabled: false }));
  });

  it("suppression : confirmation explicite puis DELETE Core", async () => {
    mockList.mockResolvedValue([makeRule()]);
    mockDelete.mockResolvedValue({ status: "deleted" });

    renderWorkspace();

    fireEvent.click(await screen.findByRole("button", { name: /Supprimer/ }));
    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Supprimer" }));

    await waitFor(() => expect(mockDelete).toHaveBeenCalledWith("a1"));
  });

  it("création : le JSON saisi est parsé et transmis au Core", async () => {
    mockList.mockResolvedValue([]);
    mockCreate.mockResolvedValue(makeRule({ name: "Ma règle" }));

    renderWorkspace();
    await screen.findByText("Aucune automation");

    fireEvent.click(screen.getByRole("button", { name: /Nouvelle automation/ }));
    fireEvent.change(screen.getByPlaceholderText("ex: résumé quotidien"), {
      target: { value: "Ma règle" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Créer/ }));

    await waitFor(() =>
      expect(mockCreate).toHaveBeenCalledWith({
        name: "Ma règle",
        description: "",
        trigger: { type: "manual" },
        actions: [],
      }),
    );
  });

  it("JSON invalide : erreur locale, aucun appel Core", async () => {
    mockList.mockResolvedValue([]);

    renderWorkspace();
    await screen.findByText("Aucune automation");

    fireEvent.click(screen.getByRole("button", { name: /Nouvelle automation/ }));
    fireEvent.change(screen.getByPlaceholderText("ex: résumé quotidien"), {
      target: { value: "X" },
    });
    const textareas = screen.getAllByRole("textbox");
    // 0 = Nom, 1 = Description, 2 = Trigger, 3 = Actions
    fireEvent.change(textareas[2], { target: { value: "{ pas du json" } });
    fireEvent.click(screen.getByRole("button", { name: /Créer/ }));

    expect(
      await screen.findByText("Trigger et actions doivent être du JSON valide."),
    ).toBeInTheDocument();
    expect(mockCreate).not.toHaveBeenCalled();
  });
});
