/**
 * Tests — palette Ctrl+K : les destinations viennent de la taxinomie unique.
 *
 * Contrat : taper « library » doit proposer `/library`, sans seconde liste de
 * navigation. La palette ne fait que filtrer `NAV_ITEMS_FLAT` (nav-config) :
 * une entrée = une destination, comme la sidebar et l'en-tête.
 */
import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";

const pushMock = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: jest.fn(), prefetch: jest.fn() }),
}));

// Le dictionnaire réel n'est pas l'objet testé : on rend la clé, qui contient
// déjà le mot recherché (`navigation.library`).
jest.mock("@/lib/i18n", () => ({
  useI18n: () => ({ t: (key: string) => key }),
}));

import { CommandPalette } from "@/components/ui/command-palette";
import { useUIStore } from "@/store/ui.store";

beforeEach(() => {
  pushMock.mockClear();
  useUIStore.setState({ commandPaletteOpen: true });
});

afterEach(() => {
  useUIStore.setState({ commandPaletteOpen: false });
});

describe("CommandPalette — destinations de navigation", () => {
  it("reconnaît Library et pointe /library", () => {
    render(<CommandPalette />);

    fireEvent.change(screen.getByPlaceholderText(/command or search/i), {
      target: { value: "library" },
    });

    const link = screen.getByRole("link", { name: /library/i });
    expect(link.getAttribute("href")).toBe("/library");
  });

  it("ne propose aucune destination quand la requête ne correspond à rien", () => {
    render(<CommandPalette />);

    fireEvent.change(screen.getByPlaceholderText(/command or search/i), {
      target: { value: "zzzz-introuvable" },
    });

    expect(screen.queryAllByRole("link")).toHaveLength(0);
  });
});
