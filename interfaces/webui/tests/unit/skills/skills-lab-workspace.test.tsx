import * as React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests de la page Skill Lab (/skills/lab) — contrat d'interface uniquement.
 *
 * Le test du code candidat se fait dans la sandbox Docker du Core
 * (POST /v1/skills/lab/test) et l'historique provient du Core
 * (GET /v1/skills/lab/results) : seul le client API est mocké. Invariants :
 * aucun repli local si Docker manque (503 affiché tel quel) et historique
 * rafraîchi après chaque test.
 */

const mockTestSkillCode = jest.fn();
const mockListResults = jest.fn();

jest.mock("@/lib/api/skills", () => ({
  testSkillCode: (...a: unknown[]) => mockTestSkillCode(...a),
  listSkillLabResults: (...a: unknown[]) => mockListResults(...a),
}));

// Import APRÈS les mocks.
import { SkillsLabWorkspace } from "@/components/features/skills/components/skills-lab-workspace";
import type { SkillLabResult } from "@/lib/api/skills";

function makeResult(over: Partial<SkillLabResult> = {}): SkillLabResult {
  return {
    id: "lab_1",
    skill_name: "test_skill",
    status: "passed",
    passed: true,
    output: "echo: bonjour",
    error: "",
    duration_ms: 420.4,
    details: {},
    timestamp: "2026-01-01T10:00:00.000Z",
    ...over,
  };
}

function renderLab() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <SkillsLabWorkspace />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("SkillsLabWorkspace — historique réel du Core", () => {
  it("aucun test enregistré : état vide explicite", async () => {
    mockListResults.mockResolvedValue([]);

    renderLab();

    expect(await screen.findByText(/Aucun test enregistré/)).toBeInTheDocument();
  });

  it("affiche les résultats conservés par le SkillLab du Core", async () => {
    mockListResults.mockResolvedValue([makeResult({ skill_name: "ma_skill" })]);

    renderLab();

    expect(await screen.findByText("ma_skill")).toBeInTheDocument();
    expect(screen.getByText(/420 ms/)).toBeInTheDocument();
  });

  it("erreur Core : message + Réessayer relance", async () => {
    mockListResults.mockRejectedValueOnce(new Error("core indisponible")).mockResolvedValue([]);

    renderLab();

    expect(await screen.findByText("Impossible de charger l'historique")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Réessayer" }));

    await waitFor(() => expect(mockListResults).toHaveBeenCalledTimes(2));
  });
});

describe("SkillsLabWorkspace — test sandboxé par le Core", () => {
  it("transmet code/nom/entrée/dépendances et affiche le résultat réel", async () => {
    mockListResults.mockResolvedValue([]);
    mockTestSkillCode.mockResolvedValue(makeResult());

    renderLab();
    await screen.findByText(/Aucun test enregistré/);

    // Ordre des champs : 0 = Nom, 1 = Code, 2 = Entrée, 3 = Dépendances.
    const fields = screen.getAllByRole("textbox");
    fireEvent.change(fields[0], { target: { value: "ma_skill" } });
    fireEvent.change(fields[1], { target: { value: "def run(input):\n    return input" } });
    fireEvent.change(fields[2], { target: { value: "bonjour" } });
    fireEvent.change(fields[3], { target: { value: "requests, pandas" } });

    fireEvent.click(screen.getByRole("button", { name: /Lancer le test/ }));

    await waitFor(() =>
      expect(mockTestSkillCode).toHaveBeenCalledWith("def run(input):\n    return input", {
        name: "ma_skill",
        input: "bonjour",
        requirements: ["requests", "pandas"],
      }),
    );
    expect(await screen.findByText("Réussi")).toBeInTheDocument();
    expect(screen.getByText("echo: bonjour")).toBeInTheDocument();
    // Le Core enregistre chaque test : l'historique est rafraîchi après coup.
    await waitFor(() => expect(mockListResults).toHaveBeenCalledTimes(2));
  });

  it("Docker absent (503) : message explicite, aucun repli local", async () => {
    mockListResults.mockResolvedValue([]);
    mockTestSkillCode.mockRejectedValue(new Error("503 — Skill Lab indisponible"));

    renderLab();
    await screen.findByText(/Aucun test enregistré/);

    fireEvent.click(screen.getByRole("button", { name: /Lancer le test/ }));

    expect(
      await screen.findByText(
        "Skill Lab indisponible : Docker est requis sur le serveur (sandbox obligatoire).",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Réussi")).not.toBeInTheDocument();
  });
});
