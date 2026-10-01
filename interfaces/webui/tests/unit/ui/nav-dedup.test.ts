/**
 * Garde-fous « menus redondants » — taxinomie de navigation (présentation seule).
 *
 * Contexte (refonte UX) : le même besoin ne doit jamais apparaître sous deux
 * entrées de menu différentes (cas historique « Models / AI Models / LLM /
 * Model Configuration », et l'entrée « Interface » qui redirigeait vers la page
 * Settings elle-même via `#appearance`).
 *
 * Invariants vérifiés ici — PILOTES PAR LES DONNÉES de `nav-config` :
 *  1. une entrée = une destination : aucun href en doublon après normalisation
 *     (`#hash` et `?query` retirés) ;
 *  2. aucun libellé en doublon entre entrées du même menu (deux « Knowledge »
 *     = ambiguity de clic) ;
 *  3. aucune entrée de menu ne pointe un hash de `/settings` (le lien profond
 *     par hash reste supporté par la page, mais n'est PLUS une entrée) ;
 *  4. les séquences clavier « G puis x » ne conduisent que vers des
 *     destinations existant dans la taxinomie (la barre latérale ou le logo
 *     couvrent la seule exception documentée : la page chat « / »).
 *
 * Règle AGENTS.md : aucune logique métier — ce test confronte des données de
 * présentation entre elles. La légitimité d'une capacité reste en Core.
 */
import fs from "fs";
import path from "path";
import { NAV_ITEMS_FLAT, NAV_SECTIONS, G_SEQUENCE_ROUTES } from "@/components/layout/nav-config";
import { SECTIONS } from "@/components/features/settings/components/settings-workspace";
import { SETTINGS_GROUPS } from "@/components/features/settings/settings-nav";

/** Destination d'un href : sans hash, sans query, sans slash final. */
const destination = (href: string): string => {
  const clean = href.split(/[#?]/)[0];
  return clean.length > 1 && clean.endsWith("/") ? clean.slice(0, -1) : clean;
};

describe("nav-config — anti-doublon des menus", () => {
  it("une entrée = une destination (aucun href en doublon après normalisation)", () => {
    const destinations = NAV_ITEMS_FLAT.map((item) => destination(item.href));
    const seen = new Set<string>();
    const duplicates = destinations.filter((d) => (seen.has(d) ? true : (seen.add(d), false)));
    expect({ entries: destinations.length, duplicates }).toEqual({
      entries: destinations.length,
      duplicates: [],
    });
  });

  it("aucun libellé en doublon entre entrées du menu", () => {
    const labels = NAV_ITEMS_FLAT.map((item) => item.label.trim().toLowerCase());
    const seen = new Set<string>();
    const duplicates = labels.filter((l) => (seen.has(l) ? true : (seen.add(l), false)));
    expect({ entries: labels.length, duplicates }).toEqual({
      entries: labels.length,
      duplicates: [],
    });
  });

  it("aucune entrée ne pointe un hash de la page Settings (entrée = destination)", () => {
    const offenders = NAV_ITEMS_FLAT.filter(
      (item) => item.href.split(/[#?]/)[0] === "/settings" && item.href !== "/settings",
    );
    expect(offenders).toEqual([]);
  });

  it("les séquences G conduisent à des destinations de la taxinomie", () => {
    const known = new Set(NAV_ITEMS_FLAT.map((item) => destination(item.href)));
    // Exception documentée : « G A » ouvre la page chat, dessinée par le logo
    // de la sidebar et non par une entrée de taxinomie.
    known.add("/");
    const unknown = Object.entries(G_SEQUENCE_ROUTES)
      .filter(([, { route }]) => !known.has(destination(route)))
      .map(([key, { route }]) => `${key} → ${route}`);
    expect(unknown).toEqual([]);
  });
});

describe("nav-config — taxinomie cohérente avec l'App Router", () => {
  const APP_DIR = path.resolve(__dirname, "../../../src/app");

  /** Dossier `page.tsx` correspondant à une destination (segments statiques). */
  const routeExists = (href: string): boolean => {
    const clean = destination(href);
    if (clean === "/") return fs.existsSync(path.join(APP_DIR, "page.tsx"));
    const target = path.join(APP_DIR, clean.replace(/^\//, ""));
    return fs.existsSync(path.join(target, "page.tsx")) || fs.existsSync(target);
  };

  it("chaque entrée de chaque section pointe une route réellement déclarée", () => {
    const missing = NAV_SECTIONS.flatMap((section) =>
      section.items.filter((item) => !routeExists(item.href)).map((item) => item.href),
    );
    expect(missing).toEqual([]);
  });
});

describe("vocabulaire canonique — fin des synonymes de menu", () => {
  /**
   * Le brief UX listait l'anti-pattern historique :
   * « Models / AI Models / LLM / Model Configuration » = UNE capacité,
   * N entrées de menu. On compare ici les libellés des TROIS surfaces de
   * navigation (palette/sidebar, sections Settings, groupes Settings) dans
   * une seule bassine, dé-doublonnés : ce qui compte est la coexistence de
   * DEUX LIBELLÉS DIFFÉRENTS pour la même idée — pas leur répétition entre
   * surfaces (motif « overview + workspace », autorisé et documenté).
   */
  const ALL_LABELS = Array.from(
    new Set(
      [
        ...NAV_ITEMS_FLAT.map((i) => i.label),
        ...SECTIONS.map((s) => s.label),
        ...SETTINGS_GROUPS.map((g) => g.label),
      ].map((label) => label.trim().toLowerCase()),
    ),
  );

  /** Ensembles de synonymes qui ne doivent JAMAIS coexister. */
  const SYNONYM_SETS: readonly (readonly string[])[] = [
    ["models", "ai models", "llm", "model configuration", "models configuration", "model settings"],
    ["providers", "llm providers", "api providers", "model providers"],
    ["knowledge", "knowledge base", "knowledge center", "documents"],
    ["skills", "skill configuration"],
    ["security", "security settings", "authentication", "authentification"],
    ["integrations", "connections", "connectors"],
    ["appearance", "interface", "theme"],
  ];

  it("aucun ensemble de synonymes ne coexiste entre menus et Settings", () => {
    const violations = SYNONYM_SETS.map((set) => ({
      capability: set[0],
      present: set.filter((label) => ALL_LABELS.includes(label)),
    })).filter((v) => v.present.length > 1);
    expect(violations).toEqual([]);
  });

  it("les libellés de sections Settings sont uniques (hors casse)", () => {
    const labels = SECTIONS.map((s) => s.label.trim().toLowerCase());
    expect(new Set(labels).size).toBe(labels.length);
  });

  it("les libellés de groupes Settings sont uniques (hors casse)", () => {
    const labels = SETTINGS_GROUPS.map((g) => g.label.trim().toLowerCase());
    expect(new Set(labels).size).toBe(labels.length);
  });
});
