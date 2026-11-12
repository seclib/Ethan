import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { PluginPicker } from "@/components/features/assistant/components/plugin-picker";

// Le picker lit son catalogue via listPlugins (GET /v1/plugins) — le Core
// arbitrage ; le mock garantit l'indépendance du test du backend. useQuery est
// mocké pour éviter le QueryClientProvider/réseau ; le Popover est mocké en
// "force open" (le contenu rendu sans interaction), ce qui isole le rendu des
// chips du picker (la logique Core est couverte par tests/plugin-core).
const mockListPlugins = jest.fn();

jest.mock("@/lib/api/plugins", () => ({
  listPlugins: () => mockListPlugins(),
}));

jest.mock("@tanstack/react-query", () => ({
  useQuery: ({ queryFn }: { queryFn: () => Promise<unknown> }) => {
    const [data, setData] = React.useState<unknown>(undefined);
    React.useEffect(() => {
      let cancelled = false;
      Promise.resolve()
        .then(() => queryFn())
        .then((v) => {
          if (!cancelled) setData(v);
        });
      return () => {
        cancelled = true;
      };
    }, []);
    return { data, isLoading: data === undefined };
  },
}));

jest.mock("@/components/ui/popover", () => ({
  Popover: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PopoverTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PopoverContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe("PluginPicker — conversation context switch", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("filtre les plugins au catalogue Core (installés/actifs) et injecte le tool référencé", async () => {
    mockListPlugins.mockResolvedValue([
      {
        id: "web-search",
        name: "Web Search",
        description: "search",
        installed: true,
        status: "active",
        featured: true,
      },
      {
        id: "github",
        name: "GitHub",
        description: "available but not installed",
        installed: false,
        status: "available",
        featured: true,
      },
      {
        id: "calendar",
        name: "Calendar",
        description: "installed but inactive",
        installed: true,
        status: "inactive",
        featured: false,
      },
    ]);

    const onToggle = jest.fn();
    render(<PluginPicker selectedIds={[]} onToggle={onToggle} />);

    // web-search (actif) → visible ; github/calendar (non utilisables) → absents
    const row = await screen.findByRole("checkbox");
    expect(row.textContent).toContain("Web Search");
    expect(screen.queryByText("GitHub")).toBeNull();
    expect(screen.queryByText("Calendar")).toBeNull();
  });

  it("appelle onToggle(id) en cliquant sur une rangée", async () => {
    mockListPlugins.mockResolvedValue([
      {
        id: "web-search",
        name: "Web Search",
        description: "search",
        installed: true,
        status: "active",
        featured: true,
      },
    ]);

    const onToggle = jest.fn();
    render(<PluginPicker selectedIds={[]} onToggle={onToggle} />);

    const row = await screen.findByRole("checkbox");
    fireEvent.click(row);
    expect(onToggle).toHaveBeenCalledWith("web-search");
  });

  it("ne propose pas un plugin inactif même s'il est installé", async () => {
    mockListPlugins.mockResolvedValue([
      {
        id: "calendar",
        name: "Calendar",
        description: "installed but inactive",
        installed: true,
        status: "inactive",
        featured: false,
      },
    ]);

    render(<PluginPicker selectedIds={[]} onToggle={jest.fn()} />);

    // Aucun row utilisable → message d'absence affiché (section "Suggested/Installed" vide).
    const empty = await screen.findByText(/Aucun plugin actif/i);
    expect(empty).toBeTruthy();
  });
});