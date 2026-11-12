/**
 * Tests — navigation Library : Workspaces, jamais Knowledges.
 *
 * La Library est une capacité de premier niveau (`/library`), pas un onglet de
 * KnowledgeHub. Ces tests portent sur la DONNÉE de navigation (nav-config),
 * consommée par l'en-tête et la palette : aucune logique métier (AGENTS.md).
 */
import fs from "fs";
import path from "path";
import { NAV_ITEMS_FLAT, NAV_SECTIONS } from "@/components/layout/nav-config";
import en from "@/locales/en.json";
import fr from "@/locales/fr.json";

describe("nav-config — Library dans la taxinomie Workspaces", () => {
  it("expose /library exactement une fois (aucun doublon)", () => {
    const entries = NAV_ITEMS_FLAT.filter((item) => item.href === "/library");
    expect(entries).toHaveLength(1);
  });

  it("ne classe pas Library dans la section Knowledge", () => {
    const knowledge = NAV_SECTIONS.find((section) => section.id === "knowledge");
    expect(knowledge).toBeDefined();
    expect(knowledge?.items.some((item) => item.href === "/library")).toBe(false);
  });

  it("porte la clé i18n navigation.library, jamais un libellé en dur", () => {
    const entry = NAV_ITEMS_FLAT.find((item) => item.href === "/library");
    expect(entry?.label).toBe("navigation.library");
  });

  it("résout navigation.library en Bibliothèque (fr) et Library (en)", () => {
    const messages = { en, fr } as Record<string, { navigation?: { library?: string } }>;
    expect(messages.fr.navigation?.library).toBe("Bibliothèque");
    expect(messages.en.navigation?.library).toBe("Library");
  });

  it("pointe une route réellement déclarée par l'App Router", () => {
    const page = path.resolve(__dirname, "../../../src/app/library/page.tsx");
    expect(fs.existsSync(page)).toBe(true);
  });
});
