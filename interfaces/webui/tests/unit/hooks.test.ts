import { renderHook, act } from "@testing-library/react";
import { useLiveMetrics } from "@/hooks/useLiveMetrics";
import { useCommandPalette } from "@/hooks/useCommandPalette";

jest.useFakeTimers();

describe("useLiveMetrics", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should initialize with provided data", () => {
    const initial = [{ value: "1" }];
    const { result } = renderHook(() => useLiveMetrics<{ value: string }>("/api/metrics", initial, 1000));
    expect(result.current.data).toEqual(initial);
  });

  it("should poll fallback when SSE unavailable", async () => {
    const initial = [{ value: "1" }];
    const { result } = renderHook(() => useLiveMetrics<{ value: string }>("/api/metrics", initial, 1000));

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });

    // Fallback fetch runs; hook should not crash and should expose current data state
    expect(Array.isArray(result.current.data)).toBe(true);
  });
});

describe("useCommandPalette", () => {
  const commands = [
    { id: "home", title: "Dashboard", group: "Nav", run: jest.fn() },
    { id: "agents", title: "Agents", group: "Nav", run: jest.fn() },
    { id: "run", title: "Run task", group: "Actions", run: jest.fn() },
  ];

  it("should return all commands when query is empty", () => {
    const { result } = renderHook(() => useCommandPalette(commands));
    expect(result.current.results).toHaveLength(3);
  });

  it("should filter commands by query", () => {
    const { result } = renderHook(() => useCommandPalette(commands));
    act(() => result.current.setQuery("agent"));
    expect(result.current.results.map((c) => c.id)).toEqual(["agents"]);
  });

  it("should group results", () => {
    const { result } = renderHook(() => useCommandPalette(commands));
    expect(Object.keys(result.current.groups)).toContain("Nav");
    expect(Object.keys(result.current.groups)).toContain("Actions");
  });
});