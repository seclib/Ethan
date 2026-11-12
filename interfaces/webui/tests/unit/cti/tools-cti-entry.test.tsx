import * as React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToolsWorkspace } from "@/components/features/tools/components/tools-workspace";
import { listAgents } from "@/lib/api/agents";
import { listTools } from "@/lib/api/tools";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api/agents", () => ({ listAgents: jest.fn() }));
jest.mock("@/lib/api/tools", () => ({
  listTools: jest.fn(),
  createTool: jest.fn(),
  deleteTool: jest.fn(),
}));

describe("Tools ETHAN-CTI entry", () => {
  beforeEach(() => {
    mockPush.mockClear();
    (listTools as jest.Mock).mockResolvedValue([]);
    (listAgents as jest.Mock).mockResolvedValue([]);
  });

  it("opens the ETHAN-CTI application route from Tools", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <ToolsWorkspace />
      </QueryClientProvider>,
    );
    fireEvent.click(await screen.findByRole("button", { name: /ETHAN-CTI/ }));
    expect(mockPush).toHaveBeenCalledWith("/tools/cti");
  });
});
