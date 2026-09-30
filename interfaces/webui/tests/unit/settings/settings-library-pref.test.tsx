/**
 * Tests — Settings → Library : préférence d'affichage réellement appliquée.
 *
 * Contrat (audit anti-fantôme 2026-09-30) : la seule préférence Library est le
 * mode d'affichage par défaut, persisté et réellement lu par /library. Les
 * préférences inventées (Auto-refresh, Show Preview) ont été supprimées.
 */
import { render, screen, fireEvent } from "@testing-library/react";
import { LibrarySection } from "../../../src/components/features/settings/components/settings-sections";
import { useLibraryStore } from "../../../src/store/library.store";

beforeEach(() => {
  useLibraryStore.setState({ viewMode: "grid" });
});

describe("Settings → Library", () => {
  it("affiche la préférence persistée et la modifie réellement", () => {
    render(<LibrarySection />);

    expect(screen.getByRole("button", { name: /Grille/ }).getAttribute("aria-pressed")).toBe("true");

    fireEvent.click(screen.getByRole("button", { name: /Liste/ }));

    expect(useLibraryStore.getState().viewMode).toBe("list");
    expect(screen.getByRole("button", { name: /Liste/ }).getAttribute("aria-pressed")).toBe("true");
  });

  it("pointe vers le workspace /library (source unique des ressources)", () => {
    render(<LibrarySection />);

    const link = screen.getByRole("link", { name: /Ouvrir la Library/ });
    expect(link.getAttribute("href")).toBe("/library");
  });

  it("n'expose plus les préférences fantômes historiques", () => {
    render(<LibrarySection />);

    expect(screen.queryByText(/Auto-refresh/i)).toBeNull();
    expect(screen.queryByText(/Show Preview/i)).toBeNull();
    expect(screen.queryByText(/Default View/i)).toBeNull();
  });
});
