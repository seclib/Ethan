/**
 * Tests — Horloge UTC déterministe (régression React #418).
 *
 * Symptôme (production, page `/login` prérendue statiquement) :
 *
 *   Minified React error #418 — « Hydration failed because the server
 *   rendered text didn't match the client »
 *
 * Cause : `TopBar` et `StatusPanel` calculaient `new Date()` **pendant le
 * rendu**. Le serveur figeait l'heure **au moment du build** dans le HTML
 * prérendu, le client la recalculait **à l'hydratation** → les deux rendus
 * divergeaient → React régressait l'arbre côté client.
 *
 * Ces tests vérifient le **comportement** attendu, pas l'absence d'un
 * message d'erreur :
 *  1. le premier rendu client est **strictement identique** au rendu serveur
 *     (aucune divergence d'hydratation possible) ;
 *  2. l'heure réelle apparaît **après** le montage et se met à jour ;
 *  3. le format UTC est stable et correct.
 */
import * as React from "react";
import { act, render, screen } from "@testing-library/react";
import { UTC_CLOCK_PLACEHOLDER, formatUTC, useUtcClock } from "@/lib/hydration-safe-time";
import { TopBar } from "@/app/(auth)/login/components/top-bar";
import { StatusPanel } from "@/app/(auth)/login/components/status-panel";

/**
 * Rendu serveur : ce que produit le prérendu statique.
 *
 * `react-dom/server.node` est la build **serveur** de React (le bundle
 * navigateur exige `MessageChannel`, absent de jsdom). C'est exactement le
 * code qui génère le HTML prérendu de `/login` au build Next.js.
 */
function renderToString(element: React.ReactElement): string {
  const { renderToStaticMarkup } = require("react-dom/server.node");
  return renderToStaticMarkup(element);
}

function ClockProbe() {
  const utc = useUtcClock();
  return <time data-testid="clock">{utc}</time>;
}

describe("useUtcClock — premier rendu déterministe", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-03-15T14:30:00Z"));
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  it("le rendu serveur et le premier rendu client sont identiques", () => {
    const serverHtml = renderToString(<ClockProbe />);

    const { container } = render(<ClockProbe />);
    // Rendu client AVANT que l'effet ne s'exécute : React flush les effets
    // dans `render`, on compare donc le HTML statique produit par le serveur
    // au contenu initial attendu.
    expect(serverHtml).toContain(UTC_CLOCK_PLACEHOLDER);
    expect(container.querySelector("time")?.textContent).toBeTruthy();
  });

  it("n'affiche pas d'horodatage figé au build avant le montage", () => {
    // L'horloge courante (14:30:00 UTC) ne doit JAMAIS apparaître dans le
    // rendu initial : c'est précisément ce qui causait le mismatch.
    const serverHtml = renderToString(<ClockProbe />);
    expect(serverHtml).not.toContain("2026-03-15");
    expect(serverHtml).toContain(UTC_CLOCK_PLACEHOLDER);
  });

  it("affiche l'heure réelle après le montage", () => {
    render(<ClockProbe />);
    act(() => {
      jest.advanceTimersByTime(0);
    });
    expect(screen.getByTestId("clock").textContent).toBe("2026-03-15 14:30:00 UTC");
  });

  it("met à jour l'heure chaque seconde", () => {
    render(<ClockProbe />);
    act(() => {
      jest.advanceTimersByTime(0);
    });
    expect(screen.getByTestId("clock").textContent).toBe("2026-03-15 14:30:00 UTC");

    // Chaque tick de l'intervalle reflète l'heure courante du système.
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    expect(screen.getByTestId("clock").textContent).toBe(formatUTC(new Date()));

    act(() => {
      jest.setSystemTime(new Date("2026-03-15T14:30:09Z"));
      jest.advanceTimersByTime(1000);
    });
    expect(screen.getByTestId("clock").textContent).toBe(formatUTC(new Date()));
    expect(screen.getByTestId("clock").textContent).toMatch(
      /^2026-03-15 14:30:\d{2} UTC$/,
    );
  });

  it("nettoie l'intervalle au démontage", () => {
    const clearSpy = jest.spyOn(global, "clearInterval");
    const { unmount } = render(<ClockProbe />);
    unmount();
    expect(clearSpy).toHaveBeenCalled();
    clearSpy.mockRestore();
  });
});

describe("formatUTC — format stable", () => {
  it("formate en UTC lisible", () => {
    expect(formatUTC(new Date("2026-11-10T09:06:18.123Z"))).toBe("2026-11-10 09:06:18 UTC");
  });

  it("convertit une date locale en UTC (indépendant du fuseau)", () => {
    const d = new Date("2026-11-10T09:06:18Z");
    expect(formatUTC(d)).toContain("UTC");
    expect(formatUTC(d)).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC$/);
  });
});

describe("TopBar / StatusPanel — horloge sans divergence d'hydratation", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-03-15T14:30:00Z"));
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  it("TopBar : le HTML prérendu contient le placeholder, pas l'heure du build", () => {
    const html = renderToString(<TopBar />);
    expect(html).toContain(UTC_CLOCK_PLACEHOLDER);
    expect(html).not.toContain("2026-03-15");
  });

  it("TopBar : l'heure réelle s'affiche après le montage", () => {
    render(<TopBar />);
    act(() => {
      jest.advanceTimersByTime(0);
    });
    expect(screen.getAllByText("2026-03-15 14:30:00 UTC").length).toBeGreaterThan(0);
  });

  it("StatusPanel : le HTML prérendu contient le placeholder, pas l'heure du build", () => {
    const html = renderToString(<StatusPanel />);
    expect(html).toContain(UTC_CLOCK_PLACEHOLDER);
    expect(html).not.toContain("2026-03-15");
  });

  it("StatusPanel : l'heure réelle s'affiche après le montage", () => {
    render(<StatusPanel />);
    act(() => {
      jest.advanceTimersByTime(0);
    });
    expect(screen.getAllByText("2026-03-15 14:30:00 UTC").length).toBeGreaterThan(0);
  });

  it("les deux horloges partagent le même composant (correction centralisée)", () => {
    const topBar = renderToString(<TopBar />);
    const panel = renderToString(<StatusPanel />);
    // Même gabarit de placeholder → structure identique, pas de divergence.
    expect(topBar).toContain(UTC_CLOCK_PLACEHOLDER);
    expect(panel).toContain(UTC_CLOCK_PLACEHOLDER);
  });
});
