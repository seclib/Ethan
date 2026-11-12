/**
 * Tests — Settings → System & Security : état réel, lecture seule.
 *
 * Contrat (audit anti-fantôme 2026-09-30) :
 *  - System révèle la santé réelle du runtime (/health/detailed + diagnostics)
 *    et pointe vers les workspaces de supervision — plus de faux réglages
 *    Log Level / Max Workers / Telemetry ;
 *  - Security révèle le statut réel (2FA, politiques, audit) et délègue la
 *    gestion au workspace /security — plus de faux toggles 2FA / API Key
 *    Rotation (aucune fausse sécurité côté UI).
 */
import * as React from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockHealth = jest.fn();
const mockDiagnostics = jest.fn();
const mockSecurity = jest.fn();
const mockTfa = jest.fn();

jest.mock("@/lib/api/diagnostics", () => ({
  fetchDetailedHealth: (...args: unknown[]) => mockHealth(...args),
  fetchDiagnostics: (...args: unknown[]) => mockDiagnostics(...args),
}));

jest.mock("@/lib/api/security", () => ({
  getSecurityStatus: (...args: unknown[]) => mockSecurity(...args),
  getTwoFactorStatus: (...args: unknown[]) => mockTfa(...args),
}));

import {
  SystemSection,
  SecuritySection,
} from "../../../src/components/features/settings/components/settings-sections";

function renderSection(node: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{node}</QueryClientProvider>);
}

beforeEach(() => {
  mockHealth.mockReset();
  mockDiagnostics.mockReset();
  mockSecurity.mockReset();
  mockTfa.mockReset();
});

describe("Settings → System (santé réelle du runtime)", () => {
  it("affiche les dépendances Core connectées", async () => {
    mockHealth.mockResolvedValue({
      status: "ok",
      checks: { api_nats: "connected", nats: "connected", redis: "connected", postgresql: "connected" },
    });
    mockDiagnostics.mockResolvedValue({
      ok: false,
      status: 503,
      message: "HTTP 503",
    });

    renderSection(<SystemSection />);

    expect(await screen.findByText("nats")).toBeInTheDocument();
    expect(screen.getByText("postgresql")).toBeInTheDocument();
    expect(screen.getAllByText("connecté")).toHaveLength(4);
    expect(screen.getByRole("link", { name: /Diagnostics/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Monitoring/ })).toBeInTheDocument();
  });

  it("état dégradé : la dépendance en erreur est affichée telle quelle", async () => {
    mockHealth.mockResolvedValue({
      status: "degraded",
      checks: { api_nats: "connected", redis: "error: timeout" },
    });
    mockDiagnostics.mockResolvedValue({ ok: false, status: 503, message: "HTTP 503" });

    renderSection(<SystemSection />);

    expect(await screen.findByText("error: timeout")).toBeInTheDocument();
  });

  it("health indisponible : message explicite (aucune valeur simulée)", async () => {
    mockHealth.mockRejectedValue(new Error("réseau"));
    mockDiagnostics.mockResolvedValue({ ok: false, status: 503, message: "HTTP 503" });

    renderSection(<SystemSection />);

    expect(await screen.findByText(/Health Core indisponible/)).toBeInTheDocument();
  });

  it("ne propose plus de faux réglages système à chaud", async () => {
    mockHealth.mockResolvedValue({ status: "ok", checks: {} });
    mockDiagnostics.mockResolvedValue({ ok: false, status: 503, message: "HTTP 503" });

    renderSection(<SystemSection />);

    await screen.findByText(/paramètres de DÉPLOIEMENT/);
    expect(screen.queryByText("Telemetry")).toBeNull();
    expect(screen.queryByText("Max Workers")).toBeNull();
    expect(screen.queryByText("Log Level")).toBeNull();
  });
});

describe("Settings → Security (état réel, gestion déléguée)", () => {
  it("affiche le statut 2FA et le résumé réel du Core", async () => {
    mockTfa.mockResolvedValue({ enabled: true, pending: false });
    mockSecurity.mockResolvedValue({
      policies: { total: 5, by_level: { high: 2 }, by_effect: { allow: 3 }, categories: [] },
      capabilities: { active: 1, subjects: [], summary: { total_evaluations: 4, allowed: 3, denied: 1 } },
      audit: { total: 42 },
    });

    renderSection(<SecuritySection />);

    expect(await screen.findByText("Activée sur ce compte.")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Gérer la sécurité/ })).toBeInTheDocument();
  });

  it("2FA indisponible : message explicite, jamais un état inventé", async () => {
    mockTfa.mockRejectedValue(new Error("403"));
    mockSecurity.mockRejectedValue(new Error("403"));

    renderSection(<SecuritySection />);

    expect(await screen.findByText(/Statut 2FA indisponible/)).toBeInTheDocument();
    expect(await screen.findByText(/Résumé sécurité indisponible/)).toBeInTheDocument();
  });

  it("ne propose AUCUN toggle de sécurité factice (fausse sécurité interdite)", async () => {
    mockTfa.mockResolvedValue({ enabled: false, pending: false });
    mockSecurity.mockRejectedValue(new Error("403"));

    renderSection(<SecuritySection />);

    await screen.findByText("Désactivée sur ce compte.");
    expect(screen.queryByText("Two-Factor Authentication")).toBeNull();
    expect(screen.queryByText("Session Timeout")).toBeNull();
    expect(screen.queryByText("API Key Rotation")).toBeNull();
  });
});
