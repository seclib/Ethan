/**
 * Tests — route `/library` : rend LibraryWorkspace directement.
 *
 * Contrat : plus de redirection vers `/knowledge?view=library`. La page est une
 * coquille de routing : toute la logique (requêtes, permissions, états) reste
 * dans `LibraryWorkspace`, qui n'est ni dupliqué ni réimplémenté.
 */
import * as React from "react";
import { render, screen } from "@testing-library/react";

const redirectMock = jest.fn();
jest.mock("next/navigation", () => ({
  redirect: (...args: unknown[]) => redirectMock(...args),
}));

jest.mock("@/components/features/library/library-workspace", () => ({
  LibraryWorkspace: () => <div data-testid="library-workspace" />,
}));

// Import après les mocks : la page est évaluée avec le routeur simulé.
import LibraryPage from "@/app/library/page";

beforeEach(() => {
  redirectMock.mockClear();
});

describe("/library — page dédiée", () => {
  it("rend LibraryWorkspace directement", () => {
    render(<LibraryPage />);
    expect(screen.getByTestId("library-workspace")).toBeTruthy();
  });

  it("n'appelle aucune redirection vers KnowledgeHub", () => {
    render(<LibraryPage />);
    expect(redirectMock).not.toHaveBeenCalled();
  });
});
