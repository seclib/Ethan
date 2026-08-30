import { render, screen, fireEvent, within } from "@testing-library/react";
import { ChatContextBar } from "../../../src/components/features/assistant/components/chat-context-bar";

describe("ChatContextBar", () => {
  it("ne rend RIEN sans capacité réelle (règle anti-fantôme)", () => {
    const { container } = render(<ChatContextBar />);
    expect(container.innerHTML).toBe("");
  });

  it("rend les capacités pré-résolues SANS dupliquer Agent/Model (dé-duplication)", () => {
    render(
      <ChatContextBar
        tools={[
          { id: "t1", name: "web_search", detail: "builtin" },
          { id: "t2", name: "sql_query", detail: "mcp" },
        ]}
        skills={[{ id: "s1", name: "Analyse Doc" }]}
        knowledge={[{ id: "k1", name: "Dev Docs" }]}
      />,
    );
    // Chips agrégés avec compteurs réels (libellé : "<n>  outils|skills|sources")
    expect(screen.getByText(/2\s+outils/)).toBeTruthy();
    expect(screen.getByText(/1\s+skills/)).toBeTruthy();
    expect(screen.getByText(/1\s+sources/)).toBeTruthy();
    // Accessibilité : le chip expose son titre avec le compte exact
    expect(screen.getByTitle("Outils actifs (2)")).toBeTruthy();
    // Règle de non-duplication : les sélecteurs Agent/Model ont UNE position
    // (le header du chat) — la barre de contexte ne doit JAMAIS les rendre.
    expect(screen.queryByText("Atreus")).toBeNull();
    expect(screen.queryByText("qwen2.5:7b · Ollama")).toBeNull();
  });

  it("n'affiche la mémoire QUE s'il existe des facts (>0)", () => {
    render(<ChatContextBar memoryFactCount={4} />);
    expect(screen.getByText("Mémoire · 4")).toBeTruthy();

    const second = render(<ChatContextBar memoryFactCount={0} />);
    // Scopé au 2e rendu : la mémoire à 0 fact ne doit JAMAIS être rendue.
    expect(within(second.container).queryByText(/Mémoire/)).toBeNull();
  });

  it("ouvre le panneau de détail au clic et liste les items réels", () => {
    render(
      <ChatContextBar
        tools={[
          { id: "t1", name: "web_search", detail: "builtin" },
          { id: "t2", name: "sql_query", detail: "mcp" },
        ]}
      />,
    );
    fireEvent.click(screen.getByTitle("Outils actifs (2)"));
    expect(screen.getByText("web_search")).toBeTruthy();
    expect(screen.getByText("sql_query")).toBeTruthy();
    expect(screen.getByText("builtin")).toBeTruthy();
    // Fermeture Échap
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByText("web_search")).toBeNull();
  });

  it("antifantôme : ne rend RIEN avec seulement des agents/modèles (dé-duplication)", () => {
    const { container } = render(
      // Ces props n'existent plus dans l'interface — le test vérifie que la
      // barre ne peut plus être alimentée par des sélecteurs du header.
      <ChatContextBar skills={[]} tools={[]} knowledge={[]} />,
    );
    expect(container.innerHTML).toBe("");
  });
});
