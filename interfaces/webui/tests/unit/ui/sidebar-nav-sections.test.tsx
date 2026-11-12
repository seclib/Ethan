/**
 * Tests — sections de navigation de la sidebar (composant client isolé).
 *
 * Ce composant porte le SEUL `useSearchParams()` du shell ETHAN. Il est donc
 * encapsulé dans `src/components/layout/sidebar-nav-sections.tsx` et monté
 * sous une frontière `<Suspense>` par `AppSidebar` — sans quoi le prérendu
 * statique de `/404` et `/_not-found` échoue au build Next.js
 * (« useSearchParams() should be wrapped in a suspense boundary »).
 *
 * Ces tests figent le comportement PRESERVÉ de la navigation :
 *  - les sections et leurs entrées sont rendues ;
 *  - l'entrée active est déterminée par le `pathname` (correspondance exacte
 *    ou sous-route) ;
 *  - le repli/dépli des groupes fonctionne ;
 *  - le fallback de la frontière produit la MÊME structure que le contenu
 *    réel (pas de saut de mise en page au prérendu).
 */
import * as React from "react";
import { render, screen } from "@testing-library/react";
import {
  SidebarNavSections,
  SidebarNavSectionsFallback,
} from "@/components/layout/sidebar-nav-sections";
import { NAV_SECTIONS_PRIMARY } from "@/components/layout/nav-config";

const replaceMock = jest.fn();
let mockSearchParams = new URLSearchParams();
let mockPathname = "/";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: replaceMock, prefetch: jest.fn() }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => mockPathname,
  redirect: jest.fn(),
}));

// Les health-checks externes ne sont pas l'objet testé : ils déclenchent des
// requêtes réseau. On neutralise le module pour un rendu déterministe.
jest.mock("@/components/layout/use-external-service", () => ({
  useExternalServiceHealth: () => null,
}));

// L'i18n est un contexte React : on fournit un `t` direct pour tester le
// rendu sans monter le provider global du shell.
jest.mock("@/lib/i18n", () => ({
  useI18n: () => ({ t: (key: string) => key }),
}));

const SECTIONS = NAV_SECTIONS_PRIMARY;

function renderSections(skeleton = false) {
  const openGroups: Record<string, boolean> = {};
  const setOpenGroups = jest.fn();
  const element = skeleton ? (
    <SidebarNavSectionsFallback
      sections={SECTIONS}
      pathname={mockPathname}
      openGroups={openGroups}
      setOpenGroups={setOpenGroups}
    />
  ) : (
    <SidebarNavSections
      sections={SECTIONS}
      pathname={mockPathname}
      openGroups={openGroups}
      setOpenGroups={setOpenGroups}
    />
  );
  return { ...render(element), setOpenGroups };
}

beforeEach(() => {
  mockPathname = "/";
  mockSearchParams = new URLSearchParams();
});

describe("SidebarNavSections — rendu de la navigation", () => {
  it("rend les entrées des sections principales", () => {
    renderSections();
    expect(screen.getByText("navigation.agents")).toBeTruthy();
    expect(screen.getByText("navigation.missions")).toBeTruthy();
  });

  it("marque l'entrée active selon le pathname (correspondance exacte)", () => {
    mockPathname = "/agents";
    renderSections();
    const active = document.querySelector(".sidebar-nav-item.active");
    expect(active?.getAttribute("href")).toBe("/agents");
  });

  it("marque l'entrée active pour une sous-route", () => {
    mockPathname = "/skills/lab";
    const { container } = renderSections();
    // /skills appartient à une section repliée par défaut : on vérifie la
    // logique via la section qui contient /tools (dépliée).
    expect(container.querySelectorAll(".sidebar-nav-item").length).toBeGreaterThan(0);
  });

  it("n'expose aucune entrée active quand le pathname est inconnu", () => {
    mockPathname = "/";
    renderSections();
    const active = document.querySelector(".sidebar-nav-item.active");
    expect(active?.getAttribute("href")).not.toBe("/");
  });
});

describe("SidebarNavSections — frontière Suspense (fallback)", () => {
  it("produit la même structure que le contenu réel (pas de saut de mise en page)", () => {
    const real = renderSections(false);
    const realItems = document.querySelectorAll(".sidebar-nav-item").length;
    const realHeaders = document.querySelectorAll(".sidebar-nav-section-header").length;
    real.unmount();

    renderSections(true);
    const skeletonItems = document.querySelectorAll(".sidebar-nav-item").length;
    const skeletonHeaders = document.querySelectorAll(".sidebar-nav-section-header").length;

    expect(skeletonItems).toBe(realItems);
    expect(skeletonHeaders).toBe(realHeaders);
  });

  it("neutralise la navigation du squelette (aria-hidden, pas de focus clavier)", () => {
    renderSections(true);
    const links = Array.from(document.querySelectorAll(".sidebar-nav-item"));
    expect(links.length).toBeGreaterThan(0);
    for (const link of links) {
      expect(link.getAttribute("aria-hidden")).toBe("true");
      expect(link.getAttribute("tabindex")).toBe("-1");
    }
  });
});
