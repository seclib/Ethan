import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";

/**
 * Cohérence des raccourcis globaux — séquences « g puis x ».
 *
 * Deux surfaces annoncent les MÊMES raccourcis :
 *  - l'indicateur visuel de GlobalShortcuts (découvrabilité) ;
 *  - la palette Ctrl+K (raccourci affiché à côté de la commande).
 * Les deux sont générées depuis G_SEQUENCE_ROUTES (source unique de vérité,
 * nav-config) et le handler clavier résout depuis cette même source.
 *
 * Invariant verrouillé ici : tout raccourci ANNONCÉ résout vers une route.
 * (Le garde-fou statique internal-links.test.ts vérifie, lui, que chaque route
 * ciblée existe réellement dans l'App Router.)
 */

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

let paletteOpen = false;

jest.mock("@/store/ui.store", () => ({
  useUIStore: () => ({
    toggleSidebar: jest.fn(),
    commandPaletteOpen: paletteOpen,
    openCommandPalette: jest.fn(),
    closeCommandPalette: jest.fn(),
    toggleInspector: jest.fn(),
  }),
}));

// Imports APRÈS les mocks.
import { GlobalShortcuts } from "@/components/layout/global-shortcuts";
import { GlobalCommandPalette } from "@/components/layout/global-command-palette";
import { G_SEQUENCE_ROUTES, formatGSequence } from "@/components/layout/nav-config";

beforeAll(() => {
  // jsdom n'implémente pas scrollIntoView (utilisé par la palette pour suivre
  // la sélection clavier).
  Element.prototype.scrollIntoView = jest.fn();
});

beforeEach(() => {
  mockPush.mockClear();
  paletteOpen = false;
});

describe("G_SEQUENCE_ROUTES — invariants de la source unique", () => {
  it("chaque séquence a une route interne et un libellé", () => {
    const entries = Object.entries(G_SEQUENCE_ROUTES);
    expect(entries.length).toBeGreaterThanOrEqual(8);
    for (const [key, sequence] of entries) {
      expect(key).toMatch(/^[a-z]$/);
      expect(sequence.route.startsWith("/")).toBe(true);
      expect(sequence.label.trim().length).toBeGreaterThan(0);
    }
  });

  it("formatGSequence produit le libellé affiché par la palette", () => {
    expect(formatGSequence("l")).toBe("G L");
    expect(formatGSequence("a")).toBe("G A");
  });
});

describe("GlobalShortcuts — le handler résout chaque séquence annoncée", () => {
  it("g puis x navigue vers la route de la source unique", () => {
    render(<GlobalShortcuts />);
    for (const [key, sequence] of Object.entries(G_SEQUENCE_ROUTES)) {
      mockPush.mockClear();
      fireEvent.keyDown(window, { key: "g" });
      fireEvent.keyDown(window, { key });
      expect(mockPush).toHaveBeenCalledWith(sequence.route);
    }
  });

  it("l'indicateur affiche toutes les séquences (aucune dérive possible)", () => {
    render(<GlobalShortcuts />);
    fireEvent.keyDown(window, { key: "g" });
    const indicator = screen.getByRole("status");
    // 10 séquences (+ le badge « G » de tête, sans classe font-mono).
    expect(indicator.querySelectorAll("kbd.font-mono")).toHaveLength(
      Object.keys(G_SEQUENCE_ROUTES).length,
    );
    const text = indicator.textContent ?? "";
    for (const sequence of Object.values(G_SEQUENCE_ROUTES)) {
      expect(text).toContain(sequence.label);
    }
  });

  it("séquence inconnue : aucune navigation, indicateur refermé", () => {
    render(<GlobalShortcuts />);
    fireEvent.keyDown(window, { key: "g" });
    expect(screen.getByRole("status")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "z" });
    expect(mockPush).not.toHaveBeenCalled();
    expect(screen.queryByRole("status")).toBeNull();
  });
});

describe("GlobalCommandPalette — raccourcis annoncés ⊆ séquences résolues", () => {
  it("n'annonce que des raccourcis G effectivement résolubles", () => {
    paletteOpen = true;
    render(<GlobalCommandPalette />);

    const options = screen.getAllByRole("option");
    const announced: string[] = [];
    for (const option of options) {
      const shortcut = option.querySelector("kbd")?.textContent?.trim() ?? "";
      if (/^G [A-Z]$/.test(shortcut)) announced.push(shortcut.slice(2).toLowerCase());
    }

    // Garde-fou du test : la palette doit bien annoncer des séquences.
    expect(announced.length).toBeGreaterThan(4);
    for (const key of announced) {
      expect(G_SEQUENCE_ROUTES[key]).toBeDefined();
    }
  });

  it("propose la Library (route réelle) et navigue dessus", () => {
    paletteOpen = true;
    render(<GlobalCommandPalette />);

    fireEvent.click(screen.getByRole("option", { name: /Go to Library/ }));
    expect(mockPush).toHaveBeenCalledWith("/library");
  });
});
