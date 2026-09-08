import * as React from "react";
import { render, screen } from "@testing-library/react";
import { McpServerDialog } from "../../../src/components/features/mcp/components/mcp-servers-workspace";

const noop = () => {};

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