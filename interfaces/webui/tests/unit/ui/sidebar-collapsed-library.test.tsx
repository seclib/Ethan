/**
 * Tests — rail replié : Library reste accessible.
 *
 * Le rail replié est volontairement minimal, mais une capacité de premier
 * niveau ne doit pas disparaître quand la sidebar est réduite : icône visible,
 * libellé traduit (title + aria-label) et état actif réel.
 */
import * as React from "react";
import { render, screen } from "@testing-library/react";

let mockPathname = "/";

jest.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("@/lib/i18n", () => ({
  useI18n: () => ({ t: (key: string) => key }),
}));

jest.mock("@/providers/auth-provider", () => ({
  useAuth: () => ({ user: null, logout: jest.fn() }),
}));

import { AppSidebar } from "@/components/layout/sidebar";

beforeAll(() => {
  // jsdom ne fournit pas matchMedia : le hook responsive en dépend.
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }),
  });
});

beforeEach(() => {
  mockPathname = "/";
});

describe("sidebar repliée — Library", () => {
  it("affiche le lien Library avec aria-label et title traduits", () => {
    render(<AppSidebar expanded={false} onToggle={jest.fn()} />);

    const link = screen.getByTestId("sidebar-collapsed-library");
    expect(link.getAttribute("href")).toBe("/library");
    expect(link.getAttribute("aria-label")).toBe("navigation.library");
    expect(link.getAttribute("title")).toBe("navigation.library");
  });

  it("marque Library actif quand le pathname est /library", () => {
    mockPathname = "/library";
    render(<AppSidebar expanded={false} onToggle={jest.fn()} />);

    expect(
      screen.getByTestId("sidebar-collapsed-library").getAttribute("aria-current"),
    ).toBe("page");
  });
});
