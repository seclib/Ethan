import { render, screen } from "@testing-library/react";
import {
  ChatGreeting,
  displayName,
  greetingFor,
} from "../../../src/components/features/assistant/components/chat-greeting";

/**
 * L'état vide du Chat doit afficher la marque ETHAN + une salutation horaire
 * nominative (« Bon après-midi, Seclib » dans la référence) et l'invite de la
 * section active — parité avec l'image de référence.
 *
 * Le logo est mocké : le test porte sur la salutation, pas sur next/image.
 */
jest.mock("../../../src/components/shared/logo", () => ({
  LogoSquare: () => <span data-testid="ethan-logo" />,
}));

// Factory autonome : `jest.mock` est hissé au-dessus des imports, donc aucune
// variable du module de test ne peut y être référencée (TDZ).
jest.mock("../../../src/providers/auth-provider", () => ({
  useAuth: () => ({ user: { name: "Seclib" } }),
}));

describe("ChatGreeting — salutation de l'état vide", () => {
  it("derive le prénom affichable depuis la session", () => {
    expect(displayName("Seclib")).toBe("Seclib");
    expect(displayName("seclib")).toBe("Seclib");
    expect(displayName("seclib@ethan.ai")).toBe("Seclib");
    expect(displayName("  John Doe ")).toBe("John");
    expect(displayName("")).toBeNull();
    expect(displayName(null)).toBeNull();
  });

  it("choisit la salutation selon l'heure locale, suffixée du prénom", () => {
    const at = (h: number) => greetingFor(new Date(2026, 0, 1, h, 0, 0), "Seclib");
    expect(at(2)).toBe("Bonne nuit, Seclib");
    expect(at(9)).toBe("Bonjour, Seclib");
    expect(at(15)).toBe("Bon après-midi, Seclib");
    expect(at(21)).toBe("Bonsoir, Seclib");
    // Sans nom exploitable : salutation seule, jamais de virgule orpheline.
    expect(greetingFor(new Date(2026, 0, 1, 15), null)).toBe("Bon après-midi");
  });

  it("rend le logo ETHAN, la salutation nominative et l'invite de la section", () => {
    render(<ChatGreeting hint="Rédaction, reformulation, style." />);

    expect(screen.getByTestId("ethan-logo")).toBeTruthy();
    // Salutation horaire réelle, suffixée du prénom de session (ici « Seclib »).
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading.textContent).toMatch(
      /^(Bonne nuit|Bonjour|Bon après-midi|Bonsoir), Seclib$/,
    );
    expect(screen.getByText("Rédaction, reformulation, style.")).toBeTruthy();
  });

  it("retombe sur l'invite par défaut sans section active", () => {
    render(<ChatGreeting />);
    expect(
      screen.getByText(/Posez une question, demandez une analyse/),
    ).toBeTruthy();
  });
});
