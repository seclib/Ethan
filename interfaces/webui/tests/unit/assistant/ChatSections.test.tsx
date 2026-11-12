import { render, screen, fireEvent } from "@testing-library/react";
import { ChatSections } from "../../../src/components/features/assistant/components/chat-sections";
import {
  CHAT_SECTIONS,
  useChatSectionStore,
} from "../../../src/store/chat-section.store";

/**
 * ChatSections est la barre située SOUS la zone de conversation :
 * Code / Apprendre / Créer / Écrire / Vie quotidienne (parité image de
 * référence : les catégories sont juste sous le composer) doivent être
 * rendues et cliquables.
 */
describe("ChatSections — catégories sous le Chat", () => {
  beforeEach(() => {
    useChatSectionStore.setState({ activeSection: "code" });
  });

  it("rend la navigation avec les 5 sections réelles", () => {
    render(<ChatSections />);

    expect(
      screen.getByRole("navigation", { name: "Sections d'utilisation" }),
    ).toBeTruthy();
    for (const section of CHAT_SECTIONS) {
      expect(screen.getByRole("button", { name: section.label })).toBeTruthy();
    }
    // Volonté non négociable : les 5 catégories de la référence.
    for (const label of ["Code", "Apprendre", "Créer", "Écrire", "Vie quotidienne"]) {
      expect(screen.getByRole("button", { name: label })).toBeTruthy();
    }
  });

  it("un CLIC active réellement la section (aria-pressed + store)", () => {
    render(<ChatSections />);

    fireEvent.click(screen.getByRole("button", { name: "Apprendre" }));

    expect(useChatSectionStore.getState().activeSection).toBe("learn");
    expect(
      screen.getByRole("button", { name: "Apprendre" }).getAttribute("aria-pressed"),
    ).toBe("true");
    expect(
      screen.getByRole("button", { name: "Code" }).getAttribute("aria-pressed"),
    ).toBe("false");
  });

  it("variant `bar` (défaut) : barre ancrée avec bordure haute, alignée à gauche", () => {
    render(<ChatSections />);

    const bar = screen.getByRole("navigation").parentElement as HTMLElement;
    expect(bar.className).toContain("border-t");
    expect(bar.className).toContain("bg-background");
    expect(screen.getByRole("navigation").className).not.toContain("justify-center");
  });

  it("variant `floating` (état vide) : chips centrés, sans chrome de barre", () => {
    render(<ChatSections variant="floating" />);

    const bar = screen.getByRole("navigation").parentElement as HTMLElement;
    // Plus de barre pleine largeur dans l'état vide (parité avec la référence).
    expect(bar.className).not.toContain("border-t");
    expect(bar.className).not.toContain("bg-background");
    expect(screen.getByRole("navigation").className).toContain("justify-center");
    // Les 5 catégories restent présentes et cliquables.
    expect(screen.getByRole("button", { name: "Écrire" })).toBeTruthy();
  });
});