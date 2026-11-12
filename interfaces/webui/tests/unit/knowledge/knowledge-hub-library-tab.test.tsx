/**
 * Tests — KnowledgeHub : Library n'est plus un onglet.
 *
 * La Library est servie par la route dédiée `/library`. Le hub conserve les
 * autres onglets et ne doit plus interpréter `?view=library` ni `#library`.
 * Les panneaux sont mockés : ce test porte sur la NAVIGATION du hub, pas sur
 * les données Core.
 */
import * as React from "react";
import { render, screen } from "@testing-library/react";
import { KnowledgeHub } from "@/components/features/knowledge/components/knowledge-hub";

jest.mock("@/components/features/folders/components/folders-workspace", () => ({
  FoldersWorkspace: () => <div data-testid="folders-panel" />,
}));
jest.mock("@/components/features/knowledge/components/knowledge-browser", () => ({
  KnowledgeBrowser: () => <div data-testid="browser-panel" />,
}));
jest.mock("@/components/features/knowledge/components/knowledge-workspace", () => ({
  KnowledgeWorkspace: () => <div data-testid="knowledge-panel" />,
}));
jest.mock("@/components/features/knowledge/components/rag-collections-view", () => ({
  RagCollectionsView: () => <div data-testid="rag-panel" />,
}));
jest.mock("@/components/features/knowledge/components/web-import-panel", () => ({
  WebImportPanel: () => <div data-testid="web-panel" />,
}));
jest.mock("@/components/features/knowledge/components/web-search-panel", () => ({
  WebSearchPanel: () => <div data-testid="web-search-panel" />,
}));
jest.mock("@/components/features/domains/components/domains-workspace", () => ({
  DomainsWorkspace: () => <div data-testid="domains-panel" />,
}));

beforeEach(() => {
  window.history.replaceState({}, "", "/knowledge");
});

describe("KnowledgeHub — plus d'onglet Library", () => {
  it("n'affiche aucun onglet Library", () => {
    render(<KnowledgeHub />);
    expect(screen.queryByRole("button", { name: /^Library$/ })).toBeNull();
  });

  it("conserve les autres onglets du hub", () => {
    render(<KnowledgeHub />);
    for (const name of [
      /Navigateur/,
      /Recherche Web/,
      /^Domains$/,
      /Tous les dossiers/,
      /Toutes les Knowledge/,
      /RAG Collections/,
      /Web Import/,
    ]) {
      expect(screen.getByRole("button", { name })).toBeTruthy();
    }
  });

  it("n'interprète plus ?view=library comme un onglet", () => {
    window.history.replaceState({}, "", "/knowledge?view=library");
    render(<KnowledgeHub />);
    expect(screen.queryByRole("button", { name: /^Library$/ })).toBeNull();
    expect(screen.getByRole("button", { name: /^Domains$/ }).getAttribute("aria-current")).toBe("page");
  });

  it("n'interprète plus #library comme un onglet", () => {
    window.history.replaceState({}, "", "/knowledge#library");
    render(<KnowledgeHub />);
    expect(screen.queryByRole("button", { name: /^Library$/ })).toBeNull();
    expect(screen.getByRole("button", { name: /^Domains$/ }).getAttribute("aria-current")).toBe("page");
  });
});
