/**
 * Tests du dialogue de fusion de dossiers (consolidation).
 *
 * Le dialogue est passif : il transmet les intentions utilisateur
 * (sources, cible, suppression explicite) au rappel fourni par le hook.
 * Aucune logique métier n'est testée ici — elle appartient au Core
 * (tests/test_folders_consolidation.py).
 */
import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MergeFoldersDialog } from "../../../src/components/features/folders/components/consolidate-dialogs";
import type { FolderTree } from "../../../src/lib/api/folders";

const tree: FolderTree[] = [
  {
    id: "f1",
    name: "Alpha",
    description: "",
    user_id: "u",
    parent_id: null,
    collection_id: null,
    icon: null,
    order: 0,
    metadata: {},
    created_at: "",
    updated_at: "",
    resource_count: 0,
    children: [
      {
        id: "f2",
        name: "Beta",
        description: "",
        user_id: "u",
        parent_id: "f1",
        collection_id: null,
        icon: null,
        order: 0,
        metadata: {},
        created_at: "",
        updated_at: "",
        resource_count: 0,
        children: [],
      },
    ],
  },
  { id: "f3", name: "Gamma", description: "", user_id: "u", parent_id: null, collection_id: null, icon: null, order: 1, metadata: {}, created_at: "", updated_at: "", resource_count: 0, children: [] },
];

describe("MergeFoldersDialog — consolidation de dossiers", () => {
  it("désactive le bouton Fusionner sans source ni cible", () => {
    render(<MergeFoldersDialog tree={tree} onMerge={jest.fn()} onClose={jest.fn()} />);
    const submit = screen.getByRole("button", { name: /Fusionner/ }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);
  });

  it("sélectionne une source, une cible et déclenche onMerge avec les bons arguments", () => {
    const onMerge = jest.fn();
    const onClose = jest.fn();
    render(<MergeFoldersDialog tree={tree} onMerge={onMerge} onClose={onClose} />);

    // Source = Alpha (checkbox source via aria-label).
    fireEvent.click(screen.getByLabelText("Sélectionner Alpha"));
    // Cible = Gamma (radio de destination, label visible).
    const gammaRadio = screen
      .getAllByRole("radio")
      .find((r) => (r.closest("label") as HTMLLabelElement)?.textContent?.includes("Gamma"));
    fireEvent.click(gammaRadio!);
    fireEvent.click(screen.getByRole("button", { name: /Fusionner \(1 → 1\)/ }));

    expect(onMerge).toHaveBeenCalledTimes(1);
    expect(onMerge).toHaveBeenCalledWith(["f1"], "f3", false);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("désactive les radios de destination correspondant aux sources", () => {
    render(<MergeFoldersDialog tree={tree} onMerge={jest.fn()} onClose={jest.fn()} />);
    fireEvent.click(screen.getByLabelText("Sélectionner Beta"));
    const radios = Array.from(document.querySelectorAll<HTMLInputElement>("input[type='radio']"));
    expect(radios.length).toBeGreaterThan(0);
    const betaRadio = radios.find((r) =>
      (r.closest("label") as HTMLLabelElement | null)?.textContent?.includes("Beta"),
    );
    expect(betaRadio?.disabled).toBe(true);
    const gammaRadio = radios.find((r) =>
      (r.closest("label") as HTMLLabelElement | null)?.textContent?.includes("Gamma"),
    );
    expect(gammaRadio?.disabled).toBe(false);
  });

  it("transmet removeSources lorsqu'il est déclenché", () => {
    const onMerge = jest.fn();
    render(<MergeFoldersDialog tree={tree} onMerge={onMerge} onClose={jest.fn()} />);
    fireEvent.click(screen.getByLabelText("Sélectionner Alpha"));
    const gammaRadio = screen
      .getAllByRole("radio")
      .find((r) => (r.closest("label") as HTMLLabelElement)?.textContent?.includes("Gamma"));
    fireEvent.click(gammaRadio!);
    fireEvent.click(screen.getByRole("checkbox", { name: /Supprimer les dossiers sources/ }));
    fireEvent.click(screen.getByRole("button", { name: /Fusionner/ }));
    expect(onMerge).toHaveBeenCalledWith(["f1"], "f3", true);
  });
});