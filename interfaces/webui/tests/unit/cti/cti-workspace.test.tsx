import * as React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CtiWorkspace } from "@/components/features/cti/cti-workspace";

jest.mock("@/lib/api/cti", () => ({
  getCtiManifest: jest.fn(),
  getCtiStatus: jest.fn(),
  listCtiObjects: jest.fn(),
  createCtiObject: jest.fn(),
}));

import { createCtiObject, getCtiManifest, getCtiStatus, listCtiObjects } from "@/lib/api/cti";

const manifest = {
  id: "ethan-cti",
  name: "ETHAN-CTI",
  version: "0.1.0",
  description: "Renseignement sur les menaces.",
  route: "/tools/cti",
  api_base: "/v1/cti",
  model: "STIX 2.1",
  capabilities: ["objects.read", "objects.create"],
};

function renderWorkspace() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <CtiWorkspace />
    </QueryClientProvider>,
  );
}

describe("ETHAN-CTI workspace", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (getCtiManifest as jest.Mock).mockResolvedValue(manifest);
    (getCtiStatus as jest.Mock).mockResolvedValue({
      status: "operational",
      service: "ethan-cti",
      model: "STIX 2.1",
      object_count: 0,
      object_count_limit: 200,
    });
    (listCtiObjects as jest.Mock).mockResolvedValue({ items: [], count: 0 });
  });

  it("shows the Core-backed app status and empty state", async () => {
    renderWorkspace();
    expect(await screen.findByText("operational")).toBeTruthy();
    expect(screen.getByText(/Aucun objet CTI/)).toBeTruthy();
  });

  it("submits a JSON STIX object to the Core API and refreshes the list", async () => {
    (createCtiObject as jest.Mock).mockResolvedValue({ id: "indicator--created" });
    (listCtiObjects as jest.Mock)
      .mockResolvedValueOnce({ items: [], count: 0 })
      .mockResolvedValueOnce({
        items: [{
          id: "indicator--created",
          owner_id: "alice",
          stix_object: { type: "indicator", name: "Test indicator" },
          created_at: "2026-10-01T00:00:00Z",
          updated_at: "2026-10-01T00:00:00Z",
        }],
        count: 1,
      });

    renderWorkspace();
    await screen.findByText("ETHAN-CTI");
    fireEvent.change(screen.getByRole("textbox", { name: "Objet STIX au format JSON" }), {
      target: { value: JSON.stringify({ type: "indicator", name: "Test indicator" }) },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enregistrer dans ETHAN Core" }));

    await waitFor(() => {
      expect((createCtiObject as jest.Mock).mock.calls[0][0]).toEqual({
        type: "indicator",
        name: "Test indicator",
      });
    });
    expect(await screen.findByText("Test indicator")).toBeTruthy();
  });

  it("surfaces API/authentication failures instead of a fake healthy screen", async () => {
    (getCtiStatus as jest.Mock).mockRejectedValue(new Error("HTTP 401"));
    renderWorkspace();
    expect(await screen.findByRole("alert")).toHaveTextContent("HTTP 401");
  });
});
