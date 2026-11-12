import * as React from "react";
import { render, screen } from "@testing-library/react";
import { McpServerDialog } from "../../../src/components/features/mcp/components/mcp-servers-workspace";
import { ToolsHub } from "../../../src/components/features/tools/components/tools-hub";

// Les hubs montent des workspaces qui utilisent `useRouter` (App Router), et
// les pages historiques appellent `redirect()`. On monte un routeur minimal :
// sinon « invariant expected app router to be mounted » — un crash
// d'infrastructure, pas un défaut de l'écran testé.
const redirectMock = jest.fn();
const replaceMock = jest.fn();
let mockSearchParams = new URLSearchParams();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: replaceMock, prefetch: jest.fn() }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => "/tools",
  redirect: (...args: unknown[]) => redirectMock(...args),
}));

// Les onglets ne sont pas l'objet testé : on mocke les DEUX workspaces
// sous-jacentes, sinon chaque test dépend du réseau et du catalogue.
jest.mock("../../../src/components/features/tools/components/tools-workspace", () => ({
  ToolsWorkspace: () => <div data-testid="tools-panel">catalogue des outils</div>,
}));
// Le dialogue reste testé pour de vrai (le masquage des secrets est un
// contrat de sécurité) : seule la liste des serveurs est simulée.
jest.mock("../../../src/components/features/mcp/components/mcp-servers-workspace", () => {
  const actual = jest.requireActual(
    "../../../src/components/features/mcp/components/mcp-servers-workspace",
  );
  return {
    ...actual,
    McpServersWorkspace: () => <div data-testid="mcp-panel">serveurs MCP</div>,
  };
});

const noop = () => {};

/**
 * MCP est une section indépendante de Workspaces (`/workspaces/mcp`) : elle
 * conserve le registre canonique `ToolServerManager` mais ne partage plus la
 * surface /tools. Ces tests figent la séparation :
 *   - ToolsHub n'expose plus que « Outils » et « Applications » ;
 *   - `/mcp` et `/tools?view=mcp` redirigent vers `/workspaces/mcp` ;
 *   - la route `/workspaces/mcp` rend bien le gestionnaire de serveurs.
 */
describe("ToolsHub — onglets Outils / Applications uniquement", () => {
  it("affiche le catalogue des outils par défaut (le cas courant)", () => {
    render(<ToolsHub />);
    expect(screen.getByRole("button", { name: /Outils/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Applications/ })).toBeTruthy();
  });

  it("n'expose plus d'onglet « Serveurs MCP » (migré dans Workspaces)", () => {
    render(<ToolsHub />);
    expect(screen.queryByRole("button", { name: /Serveurs MCP/ })).toBeNull();
  });

  it("un ?view= inconnu retombe sur le catalogue, sans écran vide", () => {
    window.history.replaceState({}, "", "/tools?view=inexistant");
    render(<ToolsHub />);
    const toolsTab = screen.getByRole("button", { name: /Outils/ });
    expect(toolsTab.getAttribute("aria-current")).toBe("page");
  });
});

/**
 * Liens profonds : les URL historiques restent VALIDES et mènent au contenu.
 * `/mcp` et `/tools?view=mcp` n'ont pas disparu — ils redirigent vers la
 * surface canonique qui expose la même ressource Core. C'est ce qui permet de
 * déplacer les écrans sans casser un signet ni un lien externe.
 */
describe("pages de redirection (URL historiques)", () => {
  // Les mocks capturés par le `jest.mock` ci-dessus : ne pas les redéclarer
  // ici, sous peine de tester une fonction jamais appelée.
  beforeEach(() => {
    redirectMock.mockClear();
    replaceMock.mockClear();
    mockSearchParams = new URLSearchParams();
  });

  it("/mcp redirige vers la section Workspaces MCP", () => {
    const Page = require("../../../src/app/mcp/page").default;
    render(<Page />);
    expect(redirectMock).toHaveBeenCalledWith("/workspaces/mcp");
  });

  it("/tools?view=mcp redirige côté client vers /workspaces/mcp", () => {
    mockSearchParams = new URLSearchParams("view=mcp");
    const Page = require("../../../src/app/tools/page").default;
    render(<Page />);
    expect(replaceMock).toHaveBeenCalledWith("/workspaces/mcp");
  });

  it("/tools sans ?view=mcp n'appelle aucune redirection", () => {
    mockSearchParams = new URLSearchParams();
    const Page = require("../../../src/app/tools/page").default;
    render(<Page />);
    expect(replaceMock).not.toHaveBeenCalled();
  });
});

describe("section Workspaces MCP", () => {
  beforeEach(() => {
    replaceMock.mockClear();
  });

  it("/workspaces/mcp rend le gestionnaire canonique des serveurs MCP", () => {
    const Page = require("../../../src/app/workspaces/mcp/page").default;
    render(<Page />);
    expect(screen.getByTestId("mcp-panel")).toBeTruthy();
  });

  it("/workspaces (parent) expose le lien vers la section MCP", () => {
    const Page = require("../../../src/app/workspaces/page").default;
    render(<Page />);
    expect(screen.getByText("Workspaces")).toBeTruthy();
    expect(screen.getByRole("link", { name: /MCP/ }).getAttribute("href")).toBe(
      "/workspaces/mcp",
    );
  });
});

describe("McpServerDialog — création/édition et masquage des secrets", () => {
  it("affiche le formulaire de création (transport + URL)", () => {
    render(<McpServerDialog server={null} onClose={noop} onSaved={noop} />);
    expect(screen.getByText("Ajouter un serveur MCP")).toBeTruthy();
    const select = screen.getByDisplayValue("HTTP");
    expect(select).toBeTruthy();
    // Champ URL requis pour HTTP.
    expect(screen.getByPlaceholderText("http://localhost:8000/sse")).toBeTruthy();
    // Bouton Créer présent.
    expect(screen.getByRole("button", { name: /Creer|Créer/ })).toBeTruthy();
  });

  it("à l'édition, le transport est en lecture seule et le token jamais affiché", () => {
    const server = {
      id: "srv-1",
      name: "filesystem",
      url: "http://localhost:8000/mcp",
      description: "Srv de test",
      auth_type: "bearer",
      auth_config: { token_set: true },
      enabled: true,
      status: "connected",
      metadata: {
        transport: "http",
        header_keys: ["Authorization"],
      },
    };
    render(<McpServerDialog server={server} onClose={noop} onSaved={noop} />);
    expect(screen.getByText("Modifier le serveur")).toBeTruthy();
    // Le transport est affiché en texte (lecture seule), pas en select.
    expect(screen.getByText(/HTTP — le transport est structurant/)).toBeTruthy();
    // Le token n'apparaît jamais en clair — seulement l'indication.
    expect(screen.getByText(/Token configure \(jamais affiche\)/)).toBeTruthy();
    // Les valeurs d'en-têtes ne sont pas affichées, seulement le nombre de clés.
    expect(screen.getByText(/1 configuree — valeurs masquees/)).toBeTruthy();
  });
});