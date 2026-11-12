import * as React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests de la page Connexions — contrat d'interface uniquement.
 *
 * Convention du repo (cf. settings-rag-navigation.test.tsx) : le VRAI
 * @tanstack/react-query est utilisé (QueryClientProvider par test) ; seul le
 * client API (@/lib/api/connections) est mocké — le test contrôle ce que le
 * Core renvoie, jamais l'HTTP.
 *
 * Règles repo-wide vérifiées :
 *  - aucun token/secret n'apparaît jamais dans le DOM ;
 *  - OAuth s'ouvre dans un nouvel onglet (window.open, noopener) ;
 *  - les 4 providers du catalogue (Email, GitHub, Medium, Notion) sont rendus
 *    avec icône, état et compte public (jamais sensible) ;
 *  - EXTENSIBILITÉ : un provider ajouté au catalogue Core apparaît sans
 *    modification de la page.
 */

const mockListProviders = jest.fn();
const mockListConnections = jest.fn();
const mockConnect = jest.fn();
const mockReconnect = jest.fn();
const mockTestConnection = jest.fn();
const mockGetPermissions = jest.fn();
const mockDisconnect = jest.fn();

jest.mock("@/lib/api/connections", () => ({
  listProviders: (...a: unknown[]) => mockListProviders(...a),
  listConnections: (...a: unknown[]) => mockListConnections(...a),
  connect: (...a: unknown[]) => mockConnect(...a),
  reconnect: (...a: unknown[]) => mockReconnect(...a),
  testConnection: (...a: unknown[]) => mockTestConnection(...a),
  getPermissions: (...a: unknown[]) => mockGetPermissions(...a),
  disconnect: (...a: unknown[]) => mockDisconnect(...a),
}));

const mockAddToast = jest.fn();

jest.mock("@/store/ui.store", () => ({
  // Hook zustand : reçoit un sélecteur — retourne la propriété sélectionnée,
  // pas l'état entier (sinon `addToast` est un objet, pas une fonction).
  useUIStore: (selector?: (s: { addToast: typeof mockAddToast }) => unknown) => {
    const state = { addToast: mockAddToast };
    return selector ? selector(state) : state;
  },
}));

/**
 * Mock lucide-react RÉSILIENT : Proxy — n'importe quel nom d'icône existe.
 * La page, ui/dialog.tsx (`X`) et ui/button.tsx importent librement ; un mock
 * à liste figée casse le rendu à la moindre icône ajoutée.
 */
jest.mock("lucide-react", () => {
  const Icon = (props: Record<string, unknown>) => (
    <span data-testid="icon" {...props} />
  );
  return new Proxy(
    { __esModule: true },
    {
      get: (target, prop) =>
        prop in target ? target[prop as keyof typeof target] : Icon,
    },
  );
});

const mockOpen = jest.fn(() => ({ closed: false, close: jest.fn() }));
window.open = mockOpen as unknown as typeof window.open;

// Import APRÈS les mocks.
import ConnectionsPage from "@/app/connections/page";

const CATALOG = [
  {
    id: "email",
    label: "Email",
    description: "Synchronisez vos emails.",
    scopes: [
      { scope: "mail.read", summary: "Lire les emails", sensitive: true },
    ],
  },
  {
    id: "github",
    label: "GitHub",
    description: "Accédez à vos dépôts.",
    scopes: [{ scope: "repo", summary: "Accès dépôts", sensitive: false }],
  },
  {
    id: "medium",
    label: "Medium",
    description: "Publiez et lisez Medium.",
    scopes: [
      { scope: "publication", summary: "Publication", sensitive: true },
      { scope: "user", summary: "Données user", sensitive: true },
      { scope: "readonly", summary: "Lecture", sensitive: false },
      { scope: "basicProfile", summary: "Profil", sensitive: false },
    ],
  },
  {
    id: "notion",
    label: "Notion",
    description: "Espaces de travail Notion.",
    scopes: [],
  },
];

function conn(provider: string, account: Record<string, unknown>) {
  return {
    id: `c-${provider}`,
    provider,
    user_id: "u1",
    status: "connected" as const,
    connected_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    scopes_requested: ["repo"],
    scopes_granted: ["repo"],
    token_expires_at: null,
    account,
    last_error: null,
  };
}

const CONNECTIONS = [
  conn("github", { login: "octocat" }),
  conn("medium", { user: "mediumuser" }),
  conn("notion", { email: "notion@exemple.com" }),
];

const AUTH_URL = "https://fake/auth?client_id=abc&state=xyz";

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ConnectionsPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  mockListProviders.mockResolvedValue(CATALOG);
  mockListConnections.mockResolvedValue(CONNECTIONS);
});

describe("ConnectionsPage — gestion des connexions externes", () => {
  it("affiche l'en-tête (même pendant le chargement) puis les 4 cartes", async () => {
    const { container } = renderPage();
    // Défaut UX corrigé : l'en-tête est visible IMMÉDIATEMENT.
    expect(
      screen.getByRole("heading", { name: "Connexions externes" }),
    ).toBeTruthy();

    await waitFor(() => screen.getByText("Email"));
    for (const label of ["Email", "GitHub", "Medium", "Notion"]) {
      expect(screen.getByText(label)).toBeTruthy();
    }
    expect(screen.getByText("Non connecté")).toBeTruthy(); // email
    expect(screen.getAllByText("Connecté").length).toBe(3);
    // Comptes publics (jamais de token) affichés sur les cartes connectées.
    expect(screen.getByText(/octocat/)).toBeTruthy();
    expect(screen.getByText(/notion@exemple\.com/)).toBeTruthy();
    expect(
      container.querySelectorAll('[data-testid="icon"]').length,
    ).toBeGreaterThan(3);
  });

  it("ANTI-FANTÔME : aucun token/secret n'apparaît dans le DOM", async () => {
    renderPage();
    await waitFor(() => screen.getByText("Email"));
    const html = document.body.innerHTML;
    for (const secret of [
      "access_token",
      "refresh_token",
      "client_secret",
      "gho_",
      "ya29.",
    ]) {
      expect(html).not.toContain(secret);
    }
  });

  it("filtre par service ou scope", async () => {
    renderPage();
    await waitFor(() => screen.getByText("Email"));
    fireEvent.change(screen.getByLabelText("Filtrer les connexions"), {
      target: { value: "git" },
    });
    expect(screen.queryByText("Email")).toBeNull();
    expect(screen.getByText("GitHub")).toBeTruthy();
  });

  it("Connecter (carte non connectée) : dialog puis OAuth en nouvel onglet", async () => {
    mockConnect.mockResolvedValue({
      connection_id: "c1",
      provider: "email",
      authorization_url: AUTH_URL,
      state: "xyz",
      scopes_requested: ["mail.read"],
    });
    renderPage();
    await waitFor(() => screen.getByText("Email"));
    fireEvent.click(screen.getByText("Email"));
    await waitFor(() => {
      expect(screen.getByText("Connecter Email")).toBeTruthy();
      expect(screen.getByText(/redirig/)).toBeTruthy();
    });
    fireEvent.click(screen.getByText(/Ouvrir l'autorisation OAuth/));
    await waitFor(() => {
      expect(mockOpen).toHaveBeenCalledWith(
        AUTH_URL,
        "_blank",
        "noopener,noreferrer",
      );
    });
  });

  it("Gérer (carte connectée) : Tester / Reconnecter / Permissions / Déconnecter", async () => {
    renderPage();
    await waitFor(() => screen.getByText("GitHub"));
    fireEvent.click(screen.getByText("GitHub"));
    await waitFor(() => {
      expect(screen.getByText("Tester")).toBeTruthy();
      expect(screen.getByText("Reconnecter")).toBeTruthy();
      expect(screen.getByText("Permissions")).toBeTruthy();
      expect(screen.getByText("Déconnecter")).toBeTruthy();
      // L'identité publique apparaît sur la carte ET dans le dialog.
      expect(screen.getAllByText(/octocat/).length).toBeGreaterThan(0);
    });
  });

  it("Tester appelle le Core", async () => {
    mockTestConnection.mockResolvedValue(CONNECTIONS[0]);
    renderPage();
    await waitFor(() => screen.getByText("GitHub"));
    fireEvent.click(screen.getByText("GitHub"));
    await waitFor(() => screen.getByText("Tester"));
    fireEvent.click(screen.getByText("Tester"));
    await waitFor(() =>
      // react-query v5 transmet un 2ᵉ argument (contexte mutation) à la fn.
      expect(mockTestConnection).toHaveBeenCalledWith(
        "github",
        expect.anything(),
      ),
    );
  });

  it("Déconnecter appelle le Core (DELETE)", async () => {
    mockDisconnect.mockResolvedValue(CONNECTIONS[0]);
    renderPage();
    await waitFor(() => screen.getByText("GitHub"));
    fireEvent.click(screen.getByText("GitHub"));
    await waitFor(() => screen.getByText("Déconnecter"));
    fireEvent.click(screen.getByText("Déconnecter"));
    await waitFor(() =>
      expect(mockDisconnect).toHaveBeenCalledWith("github", expect.anything()),
    );
  });

  it("Permissions récupérées depuis le Core", async () => {
    mockGetPermissions.mockResolvedValue({
      provider: "github",
      connection_id: "c-github",
      requested: [
        { scope: "repo", summary: "Accès dépôts", sensitive: false },
      ],
      granted: ["repo"],
    });
    renderPage();
    await waitFor(() => screen.getByText("GitHub"));
    fireEvent.click(screen.getByText("GitHub"));
    await waitFor(() => screen.getByText("Permissions"));
    fireEvent.click(screen.getByText("Permissions"));
    await waitFor(() =>
      expect(mockGetPermissions).toHaveBeenCalledWith("github"),
    );
  });

  it("EXTENSIBILITÉ : un nouveau provider du catalogue apparaît sans toucher à la page", async () => {
    mockListProviders.mockResolvedValue([
      ...CATALOG,
      {
        id: "gitlab",
        label: "GitLab",
        description: "CI/CD.",
        scopes: [{ scope: "api", summary: "API", sensitive: false }],
      },
    ]);
    renderPage();
    await waitFor(() => screen.getByText("GitLab"));
    expect(screen.getByText("GitLab").closest(".rounded-xl")).toBeTruthy();
  });
});
