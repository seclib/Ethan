/**
 * Tests — entrée Library de la sidebar (donnée de présentation).
 *
 * Contrat : Library vit dans Workspaces, juste après DAĒNĀ, et son libellé est
 * une clé i18n (`navigation.library`) — pas une chaîne en dur, sans quoi la
 * sidebar resterait anglaise en locale française.
 */
import { WORKSPACE_SECTIONS } from "@/components/layout/sidebar";

const workspaces = WORKSPACE_SECTIONS.find((section) => section.id === "workspaces");

describe("sidebar — Library dans Workspaces", () => {
  it("place Library immédiatement après DAĒNĀ", () => {
    const hrefs = workspaces?.items.map((item) => item.href) ?? [];
    expect(hrefs.slice(0, 2)).toEqual(["/workspaces/observatory", "/library"]);
  });

  it("utilise la clé de traduction navigation.library", () => {
    const entry = workspaces?.items.find((item) => item.href === "/library");
    expect(entry?.label).toBe("navigation.library");
    expect(entry?.icon).toBeDefined();
  });

  it("préserve DAĒNĀ et Skills (aucune régression de navigation)", () => {
    const hrefs = workspaces?.items.map((item) => item.href) ?? [];
    expect(hrefs).toContain("/workspaces/observatory");
    expect(hrefs).toContain("/skills");
  });

  it("n'expose qu'une seule entrée /library dans la sidebar", () => {
    const entries = workspaces?.items.filter((item) => item.href === "/library") ?? [];
    expect(entries).toHaveLength(1);
  });
});
