import { getParentPath } from "../../../src/components/layout/app-header";

describe("navigation — retour et hiérarchie", () => {
  it("pas de parent pour la racine", () => {
    expect(getParentPath("/")).toBeNull();
  });

  it("pas de parent pour une section racine", () => {
    expect(getParentPath("/settings")).toBeNull();
    expect(getParentPath("/missions")).toBeNull();
  });

  it("remonte d'un niveau sur une vue imbriquée", () => {
    expect(getParentPath("/skills/lab")).toBe("/skills");
    expect(getParentPath("/projects/123/files")).toBe("/projects/123");
  });
});
