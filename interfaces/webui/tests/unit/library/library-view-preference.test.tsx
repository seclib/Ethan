/**
 * Tests — Library : la préférence d'affichage Settings est la source unique.
 *
 * Le mode grille/liste est persisté dans `library.store` (préférence
 * d'interface) et partagé entre la page /library et Settings → Library : le
 * toggle de la page écrit la même préférence, aucune divergence possible.
 */
import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockGetLibrary = jest.fn();
jest.mock("@/lib/api/library", () => ({
  getLibrary: (...args: unknown[]) => mockGetLibrary(...args),
}));

import { LibraryWorkspace } from "@/components/features/library/library-workspace";
import { useLibraryStore } from "@/store/library.store";

function renderLibrary() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <LibraryWorkspace />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  mockGetLibrary.mockReset();
  mockGetLibrary.mockResolvedValue({ items: [], total: 0, filters: {} });
  useLibraryStore.setState({ viewMode: "grid" });
});

describe("Library — préférence d'affichage partagée", () => {
  it("applique la vue persistée (liste) à l'ouverture", async () => {
    useLibraryStore.setState({ viewMode: "list" });
    renderLibrary();

    await screen.findByText("Aucun élément dans la bibliothèque");
    expect(screen.getByLabelText("Vue liste").getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByLabelText("Vue grille").getAttribute("aria-pressed")).toBe("false");
  });

  it("le toggle de la page écrit la préférence persistée", async () => {
    renderLibrary();

    await screen.findByText("Aucun élément dans la bibliothèque");
    fireEvent.click(screen.getByLabelText("Vue liste"));

    expect(useLibraryStore.getState().viewMode).toBe("list");
  });
});
