/**
 * Tests du workspace Mission — contrat d'interface uniquement.
 *
 * Vérifie l'architecture initiale du workspace dédié :
 *  - le layout /missions expose la navigation interne (6 sections) ;
 *  - chaque section pointe vers sa route dédiée ;
 *  - les sections non implémentées (Workflows, Templates, Settings) sont
 *    marquées « soon » et n'affichent AUCUN contenu factice ;
 *  - la vue Connections affiche le catalogue réel du Core (lecture seule)
 *    et renvoie vers /connections pour la gestion ;
 *  - le Chat n'affiche plus de missions : le composant d'overlay
 *    MissionControlOverlay a été supprimé du layout racine.
 *
 * Convention du repo : le VRAI react-query ; seuls les clients API et
 * next/navigation sont mockés (cf. ConnectionsPage.test.tsx).
 */
import * as React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  usePathname: () => "/missions",
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
}));

const mockListProviders = jest.fn();
const mockListConnections = jest.fn();
jest.mock("@/lib/api/connections", () => ({
  listProviders: (...a: unknown[]) => mockListProviders(...a),
  listConnections: (...a: unknown[]) => mockListConnections(...a),
}));

const mockListMissions = jest.fn();
jest.mock("@/lib/api/missions", () => ({
  listMissions: (...a: unknown[]) => mockListMissions(...a),
  getMission: jest.fn(),
  createMission: jest.fn(),
  updateMission: jest.fn(),
  deleteMission: jest.fn(),
  verifyMissionStep: jest.fn(),
  approveMissionStep: jest.fn(),
}));

jest.mock("@/components/features/goals/hooks/use-goals", () => ({
  useGoals: () => ({ goals: [], isLoading: false, refetch: jest.fn() }),
}));

jest.mock("lucide-react", () => {
  const Icon = (props: Record<string, unknown>) => <span data-testid="icon" {...props} />;
  return new Proxy(
    { __esModule: true },
    {
      get: (target, prop) => (prop in target ? target[prop as keyof typeof target] : Icon),
    },
  );
});

// Import APRÈS les mocks.
import MissionsWorkspaceLayout from "@/app/missions/layout";
import MissionWorkflowsPage from "@/app/missions/workflows/page";
import MissionTemplatesPage from "@/app/missions/templates/page";
import MissionConnectionsPage from "@/app/missions/connections/page";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("Workspace Mission — navigation dédiée", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockListMissions.mockResolvedValue([]);
    mockListProviders.mockResolvedValue([]);
    mockListConnections.mockResolvedValue([]);
  });

  it("le layout expose les 6 sections avec leurs routes dédiées", () => {
    renderWithProviders(<MissionsWorkspaceLayout><div>contenu</div></MissionsWorkspaceLayout>);
    const nav = screen.getByRole("navigation", { name: /workspace mission/i });
    const links = Array.from(nav.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    expect(links).toEqual([
      "/missions",
      "/missions/workflows",
      "/missions/templates",
      "/missions/runs",
      "/missions/connections",
      "/missions/settings",
    ]);
  });

  it("Workflows : roadmap honnête, aucun moteur ou exécution fictive", () => {
    renderWithProviders(<MissionWorkflowsPage />);
    expect(screen.getByText(/orchestrateur visuel/i)).toBeTruthy();
    expect(screen.getByText(/Architecture prévue/i)).toBeTruthy();
    // Rien qui ressemble à un faux état d'exécution :
    expect(screen.queryByText(/running/i)).toBeNull();
    expect(screen.queryByText(/exécution en cours/i)).toBeNull();
  });

    it("Templates : placeholder honnête, aucun template fictif", () => {
    renderWithProviders(<MissionTemplatesPage />);
    expect(screen.getAllByText(/Templates/)[0]).toBeTruthy();
    expect(screen.getByText(/Architecture prévue/i)).toBeTruthy();
  });

  it("Connections : catalogue réel du Core, lecture seule + lien de gestion", async () => {
    mockListProviders.mockResolvedValue([
      {
        id: "github",
        label: "GitHub",
        description: "Accédez à vos dépôts.",
        scopes: [{ scope: "repo", summary: "Dépôts", sensitive: false }],
      },
    ]);
    mockListConnections.mockResolvedValue([
      { provider: "github", status: "connected", account_label: "octocat" },
    ]);
    renderWithProviders(<MissionConnectionsPage />);
    await waitFor(() => screen.getByText("GitHub"));
    expect(screen.getByText("connected")).toBeTruthy();
    // Lecture seule : pas de bouton de connexion ici — la gestion vit dans /connections.
    expect(screen.queryByText(/Connecter/)).toBeNull();
    expect(screen.getByText(/Gérer dans Connections/)).toBeTruthy();
  });
});