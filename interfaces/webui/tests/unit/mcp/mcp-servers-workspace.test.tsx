import * as React from "react";
import { render, screen } from "@testing-library/react";
import { McpServerDialog } from "../../../src/components/features/mcp/components/mcp-servers-workspace";
import { ToolsHub } from "../../../src/components/features/tools/components/tools-hub";
import { KnowledgeHub } from "../../../src/components/features/knowledge/components/knowledge-hub";

// Les hubs montent des workspaces qui utilisent `useRouter` (App Router), et
// les pages historiques appellent `redirect()`. On monte un routeur minimal :
// sinon « invariant expected app router to be mounted » — un crash
// d'infrastructure, pas un défaut de l'écran testé.
const redirectMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/tools",
  redirect: (...args: unknown[]) => redirectMock(...args),
}));

// Les onglets ne sont pas l'objet testé : on mocke les DEUX workspaces
// sous-jacentes, sinon chaque test dépend du réseau et du catalogue.
jest.mock("../../../src/components/features/tools/components/tools-workspace", () => ({
  ToolsWorkspace: () => <div data-testid="tools-panel">catalogue des outils</div>,
}));
// KnowledgeHub pour l'onglet Library : on simule aussi son panneau, sinon le
// test dépend du réseau et du catalogue comme d'un écran de données.
jest.mock("../../../src/components/features/library/library-workspace", () => ({
  LibraryWorkspace: () => <div data-testid="library-panel">library</div>,
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
 * Consolidation (30/09/2026) : MCP et Library sont devenus des ONGLETS de
 * surfaces qui partagent leurs endpoints Core. Ces tests figent le comportement
 * qui rend la déduplication invisible pour l'utilisateur :
 *   - l'onglet par défaut est l'outil / la connaissance (pas MCP, pas Library) ;
 *   - `?view=` ouvre le bon onglet (c'est ainsi que /mcp et /library, qui
 *     redirigent, atteignent leur contenu) ;
 *   - un `?view=` inconnu ne casse rien (retour à l'onglet par défaut).
 */
describe("ToolsHub — onglets Outils / Serveurs MCP", () => {
  const originalSearch = window.location.search;

  afterEach(() => {
    window.history.replaceState({}, "", originalSearch);
  });

  it("affiche le catalogue des outils par défaut (le cas courant)", () => {
    render(<ToolsHub />);
    expect(screen.getByRole("button", { name: /Outils/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Serveurs MCP/ })).toBeTruthy();
  });

  it("?view=mcp ouvre l'onglet des serveurs — c'est la destination de /mcp", () => {
    window.history.replaceState({}, "", "/tools?view=mcp");
    render(<ToolsHub />);
    const mcpTab = screen.getByRole("button", { name: /Serveurs MCP/ });
    expect(mcpTab.getAttribute("aria-current")).toBe("page");
  });

  it("un ?view= inconnu retombe sur le catalogue, sans écran vide", () => {
    window.history.replaceState({}, "", "/tools?view=inexistant");
    render(<ToolsHub />);
    const toolsTab = screen.getByRole("button", { name: /Outils/ });
    expect(toolsTab.getAttribute("aria-current")).toBe("page");
  });
});

describe("consolidation Knowledge/Library et Tools/MCP — un onglet, une route canonique", () => {
  it("?view=library ouvre l'onglet Library — c'est la destination de /library", () => {
    window.history.replaceState({}, "", "/knowledge?view=library");
    render(<KnowledgeHub />);
    const libraryTab = screen.getByRole("button", { name: /^Library$/ });
    expect(libraryTab.getAttribute("aria-current")).toBe("page");
  });
});

/**
 * Liens profonds : les URL historiques restent VALIDES et mènent au contenu.
 * `/library` et `/mcp` n'ont pas disparu — ils redirigent vers la surface
 * canonique qui expose la même ressource Core. C'est ce qui permet de
 * dédupliquer les écrans sans casser un signet ni un lien externe.
 */
describe("pages de redirection (URL historiques)", () => {
  // `redirectMock` est celui capturé par le `jest.mock` ci-dessus : ne pas le
  // redéclarer ici, sous peine de tester une fonction jamais appelée.
  beforeEach(() => redirectMock.mockClear());

  it("/library redirige vers l'onglet Library de /knowledge", () => {
    const Page = require("../../../src/app/library/page").default;
    render(<Page />);
    expect(redirectMock).toHaveBeenCalledWith("/knowledge?view=library");
  });

  it("/mcp redirige vers l'onglet MCP de /tools", () => {
    const Page = require("../../../src/app/mcp/page").default;
    render(<Page />);
    expect(redirectMock).toHaveBeenCalledWith("/tools?view=mcp");
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