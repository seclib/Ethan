import * as React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ApplicationCatalog } from "@/components/features/tools/components/application-catalog";

jest.mock("@/lib/api/application-integration-catalog", () => ({
  listApplicationIntegrationCatalog: jest.fn(async () => ({
    root: "/home/fatsio/AI/Ethan",
    items: [
      {
        repository_path: "examples/ComfyUI",
        repository_name: "ComfyUI",
        analysis: {},
        manifest_availability: "valid",
        manifest_validation_status: "valid",
        application_type: "web_application",
        declared_capabilities: ["runtime-observation"],
        declared_dependencies: ["docker", "python"],
        declared_permissions: ["runtime-observation"],
        required_permissions: [],
        integration_preview: null,
        registration_status: "not-registered",
        registered_identity: null,
        manifest_fingerprint: "abc",
        sources: {},
        states: {
          discovered: true,
          validated: true,
          registered: false,
          installed: "unknown",
          available: "unknown",
          running: "unknown",
          authorized: "unknown",
        },
        errors: [],
      },
    ],
    source_errors: [],
  })),
}));

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("ApplicationCatalog", () => {
  it("affiche le candidat ComfyUI renvoyé par le Core", async () => {
    renderWithClient(<ApplicationCatalog />);
    await waitFor(() => expect(screen.getByText("ComfyUI")).toBeTruthy());
    expect(screen.getAllByText(/Confirmé/).length).toBeGreaterThan(0);
    expect(screen.getByText("Manifeste validé")).toBeTruthy();
    expect(screen.getByText("web_application")).toBeTruthy();
    expect(screen.getByText("runtime-observation")).toBeTruthy();
    await waitFor(() =>
      expect(
        screen.getByText("examples/ComfyUI")
      ).toBeTruthy()
    );
  });
});
