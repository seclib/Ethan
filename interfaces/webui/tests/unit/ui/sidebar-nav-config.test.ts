/**
 * Tests — contrat de repli des groupes de la sidebar (présentation seule).
 *
 * Contexte : deux incohérences corrigées dans le shell —
 *  - le premier clic sur un groupe ouvert était INERTE : `!groups[id]` valait
 *    `true` sur un état `undefined`, alors que le défaut implicite du
 *    composant est « ouvert » (`groups[id] ?? true`) ;
 *  - l'Administration s'affichait dépliée au premier rendu, donnant à la
 *    WebUI un air de console d'administration (objectif « assistant-first »).
 *
 * Le repli par défaut est une DONNÉE de la taxinomie (`NavSection.defaultCollapsed`)
 * et la transition est une fonction pure : testables sans monter le shell.
 * Aucune logique métier n'est impliquée (AGENTS.md).
 */
import {
  NAV_SECTIONS_PRIMARY,
  NAV_SECTIONS_ADMIN,
  NAV_SECTIONS,
  initialCollapsedGroups,
  toggleGroupState,
} from "@/components/layout/nav-config";

describe("sidebar — repli des groupes (taxinomie)", () => {
  it("replie l'Administration au premier rendu (assistant-first)", () => {
    expect(initialCollapsedGroups(NAV_SECTIONS_ADMIN)).toEqual({ admin: false });
  });

  it("laisse Pilotage déployé (aucun repli par défaut)", () => {
    const operate = NAV_SECTIONS_PRIMARY.find((s) => s.id === "operate");
    expect(operate?.defaultCollapsed).toBeUndefined();
    expect(initialCollapsedGroups(NAV_SECTIONS_PRIMARY)).toEqual({});
  });

  it("invariant : toute section defaultCollapsed est forcément collapsible", () => {
    for (const section of NAV_SECTIONS) {
      if (section.defaultCollapsed) expect(section.collapsible).toBe(true);
    }
  });
});

describe("sidebar — transition de repli/dépli", () => {
  it("le premier clic sur un groupe ouvert par défaut le replie", () => {
    // « operate » n'a jamais été togglé : défaut implicite = ouvert.
    expect(toggleGroupState({}, "operate")).toEqual({ operate: false });
  });

  it("le premier clic sur l'Administration (repliée) la déplie", () => {
    expect(toggleGroupState({ admin: false }, "admin")).toEqual({ admin: true });
  });

  it("alterne ensuite normalement (2 clics = état initial)", () => {
    const once = toggleGroupState({}, "operate");
    expect(toggleGroupState(once, "operate")).toEqual({ operate: true });
  });

  it("ne modifie pas l'état des autres groupes", () => {
    expect(toggleGroupState({ admin: false }, "operate")).toEqual({
      admin: false,
      operate: false,
    });
  });
});
