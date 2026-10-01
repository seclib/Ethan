/**
 * Tests — arborescence Settings (taxinomie cible validée, présentation seule).
 *
 * Garde-fous « cartographie avant suppression » :
 *  - chaque section existante reste accessible (aucune perte silencieuse) ;
 *  - chaque section appartient à EXACTEMENT un groupe (pas de doublon) ;
 *  - l'ordre des groupes suit l'arborescence cible ;
 *  - le registre `SECTIONS` du workspace reste synchrone avec la taxinomie ;
 *  - la palette/header (nav-config) ne publie aucun href en doublon.
 *
 * Aucune logique métier n'est simulée : le module testé est une pure donnée
 * de présentation et la vérité reste dans ETHAN Core.
 */
import {
  SETTINGS_GROUPS,
  SETTINGS_SECTION_IDS,
  isSettingsSectionId,
  type SettingsSectionId,
} from "@/components/features/settings/settings-nav";
import { SECTIONS } from "@/components/features/settings/components/settings-workspace";
import { NAV_ITEMS_FLAT } from "@/components/layout/nav-config";

const TARGET_TREE_LABELS = [
  "General",
  "AI",
  "Knowledge",
  "Skills",
  "Integrations",
  "Security",
  "Appearance",
  "Advanced",
];

describe("settings-nav — arborescence cible", () => {
  it("expose exactement les 8 groupes de l'arborescence cible, dans l'ordre", () => {
    expect(SETTINGS_GROUPS.map((g) => g.label)).toEqual(TARGET_TREE_LABELS);
  });

  it("couvre chaque section exactement une fois (aucune perte, aucun doublon)", () => {
    const covered: SettingsSectionId[] = SETTINGS_GROUPS.flatMap((g) => [...g.items]);
    expect(covered).toHaveLength(SETTINGS_SECTION_IDS.length);
    expect(new Set(covered).size).toBe(covered.length);
    expect([...covered].sort()).toEqual([...SETTINGS_SECTION_IDS].sort());
  });

  it("uniquement des ids de sections connues dans les groupes (type + runtime)", () => {
    const known = new Set<string>(SETTINGS_SECTION_IDS);
    for (const group of SETTINGS_GROUPS) {
      for (const item of group.items) {
        expect(known.has(item)).toBe(true);
        expect(isSettingsSectionId(item)).toBe(true);
      }
    }
    expect(isSettingsSectionId("inconnu")).toBe(false);
  });
});

describe("registre SECTIONS du workspace", () => {
  it("déclare exactement les ids de la taxinomie (synchro registre ↔ navigation)", () => {
    const declared = SECTIONS.map((s) => s.id).sort();
    expect(declared).toEqual([...SETTINGS_SECTION_IDS].sort());
  });

  it("n'expose plus les écrans fantômes historiques (general, ai, advanced)", () => {
    // Régression : ces ids ouvraient des formulaires factices jamais branchés
    // (éditeur /v1/settings non consommé, faux Default Model/Temperature,
    // Experimental Features/Debug Mode). Voir
    // docs/design/2026-09-30-webui-settings-honesty.md.
    const ids = new Set<string>(SETTINGS_SECTION_IDS);
    for (const phantom of ["general", "ai", "advanced"]) {
      expect(ids.has(phantom)).toBe(false);
    }
  });

  it("évite les doublons en-tête/item (Preferences sous General, Experimental sous Advanced)", () => {
    const labels = new Map(SECTIONS.map((s) => [s.id, s.label]));
    // Exception documentée : « Knowledge » (overview du knowledge base) garde
    // son libellé — verrouillé par settings-rag-navigation.test.tsx (régession
    // historique : section RAG devenue code mort). L'en-tête de groupe est une
    // légende en capitales, pas un bouton : pas d'ambiguïté de clic.
    const LABEL_EXCEPTIONS = new Set<SettingsSectionId>(["knowledge"]);
    for (const group of SETTINGS_GROUPS) {
      // L'en-tête n'est rendu que pour les groupes multi-sections : un groupe
      // à section unique est affiché directement (pas de « Skills › Skills »).
      if (group.items.length <= 1) continue;
      // Un item ne porte jamais le même libellé que l'en-tête de son groupe
      // (hors exception documentée).
      const collide = group.items.some(
        (id) => labels.get(id) === group.label && !LABEL_EXCEPTIONS.has(id),
      );
      expect({ group: group.label, collide }).toEqual({ group: group.label, collide: false });
    }
  });
});

describe("nav-config — palette / header", () => {
  it("ne publie aucun href en doublon (menus redondants)", () => {
    const hrefs = NAV_ITEMS_FLAT.map((i) => i.href);
    expect(new Set(hrefs).size).toBe(hrefs.length);
  });

  // MCP = onglet de la surface unique des outils (ToolsHub). Le menu expose
  // donc /tools, pas /mcp : une ressource Core, une entrée de menu.
  it("couvre les workspaces clés du scénario réel (models, providers, knowledge, skills, tools)", () => {
    const hrefs = new Set(NAV_ITEMS_FLAT.map((i) => i.href));
    for (const href of ["/models", "/providers", "/knowledge", "/skills", "/tools"]) {
      expect(hrefs.has(href)).toBe(true);
    }
    // Les anciennes routes dédupliquées ne doivent plus être des entrées de menu.
    expect(hrefs.has("/mcp")).toBe(false);
    expect(hrefs.has("/library")).toBe(false);
  });
});
