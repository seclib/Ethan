import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { FolderNav, getFolderPath } from "../../../src/components/features/skills/components/skills-workspace";
import type { FolderTreeNode } from "../../../src/lib/api/folders";

const makeNode = (overrides: Partial<FolderTreeNode> = {}): FolderTreeNode => ({
  id: "folder_1",
  name: "Mes dossiers",
  description: "",
  user_id: "user_1",
  parent_id: null,
  collection_id: null,
  icon: null,
  order: 0,
  metadata: {},
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  resource_count: 0,
  children: [],
  ...overrides,
});

describe("getFolderPath — fil d'Ariane", () => {
  const tree: FolderTreeNode[] = [
    makeNode({ id: "f1", name: "Dossier A", children: [
      makeNode({ id: "f2", name: "Sous-dossier A1", children: [
        makeNode({ id: "f3", name: "Profond A1a" }),
      ] }),
    ] }),
    makeNode({ id: "f4", name: "Dossier B" }),
  ];

  it("retourne le chemin d'un dossier racine", () => {
    const path = getFolderPath("f1", tree);
    expect(path).toEqual([{ id: "f1", name: "Dossier A" }]);
  });

  it("retourne le chemin d'un dossier imbriqué", () => {
    const path = getFolderPath("f3", tree);
    expect(path).toEqual([
      { id: "f1", name: "Dossier A" },
      { id: "f2", name: "Sous-dossier A1" },
      { id: "f3", name: "Profond A1a" },
    ]);
  });

  it("retourne un tableau vide si le dossier est introuvable", () => {
    const path = getFolderPath("inexistant", tree);
    expect(path).toEqual([]);
  });

  it("retourne un tableau vide pour un arbre vide", () => {
    const path = getFolderPath("f1", []);
    expect(path).toEqual([]);
  });
});

describe("FolderNav — navigation et actions sur les dossiers", () => {
  const tree: FolderTreeNode[] = [
    makeNode({ id: "f1", name: "Dossier A", children: [
      makeNode({ id: "f2", name: "Sous-dossier A1" }),
    ] }),
    makeNode({ id: "f4", name: "Dossier B" }),
  ];

  const countFn = jest.fn(() => 0);

  it("affiche les dossiers avec leur nom et leur nombre de skills", () => {
    render(
      <FolderNav
        nodes={tree}
        depth={0}
        activeId=""
        countFn={countFn}
        onSelect={jest.fn()}
      />,
    );
    expect(screen.getByText("Dossier A")).toBeInTheDocument();
    expect(screen.getByText("Dossier B")).toBeInTheDocument();
    expect(screen.getByText("Sous-dossier A1")).toBeInTheDocument();
  });

  it("appelle onSelect quand on clique sur un dossier", () => {
    const onSelect = jest.fn();
    render(
      <FolderNav
        nodes={tree}
        depth={0}
        activeId=""
        countFn={countFn}
        onSelect={onSelect}
      />,
    );
    fireEvent.click(screen.getByText("Dossier B"));
    expect(onSelect).toHaveBeenCalledWith("f4");
  });

  it("appelle onCreate quand on clique sur le bouton Nouveau sous-dossier", () => {
    const onCreate = jest.fn();
    render(
      <FolderNav
        nodes={tree}
        depth={0}
        activeId=""
        countFn={countFn}
        onSelect={jest.fn()}
        onCreate={onCreate}
      />,
    );
    fireEvent.click(screen.getAllByRole("button", { name: "Nouveau sous-dossier" })[0]);
    expect(onCreate).toHaveBeenCalledWith("f1");
  });

  it("appelle onRename quand on clique sur le bouton Renommer", () => {
    const onRename = jest.fn();
    render(
      <FolderNav
        nodes={tree}
        depth={0}
        activeId=""
        countFn={countFn}
        onSelect={jest.fn()}
        onRename={onRename}
      />,
    );
    fireEvent.click(screen.getAllByRole("button", { name: "Renommer" })[0]);
    expect(onRename).toHaveBeenCalledWith("f1", "Dossier A");
  });

  it("appelle onDelete quand on clique sur le bouton Supprimer", () => {
    const onDelete = jest.fn();
    render(
      <FolderNav
        nodes={tree}
        depth={0}
        activeId=""
        countFn={countFn}
        onSelect={jest.fn()}
        onDelete={onDelete}
      />,
    );
    fireEvent.click(screen.getAllByRole("button", { name: "Supprimer le dossier" })[0]);
    expect(onDelete).toHaveBeenCalledWith("f1");
  });

  it("n'affiche pas les boutons d'action quand les props ne sont pas fournies", () => {
    render(
      <FolderNav
        nodes={tree}
        depth={0}
        activeId=""
        countFn={countFn}
        onSelect={jest.fn()}
      />,
    );
    expect(screen.queryByRole("button", { name: "Nouveau sous-dossier" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Renommer" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Supprimer le dossier" })).not.toBeInTheDocument();
  });

  it("met en évidence le dossier actif", () => {
    render(
      <FolderNav
        nodes={tree}
        depth={0}
        activeId="f1"
        countFn={countFn}
        onSelect={jest.fn()}
      />,
    );
    // Le dossier actif devrait avoir un fond accentué
    const activeButton = screen.getByText("Dossier A").closest("button");
    expect(activeButton).toHaveClass("bg-accent/10");
  });
});
